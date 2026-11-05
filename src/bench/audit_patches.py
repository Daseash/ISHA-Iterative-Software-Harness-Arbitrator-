"""
ISHA patch audit — find loopholes in produced patches before grading.

Builds the merged view across run directories (later run wins), then screens
every instance that has a patch for the failure shapes that survive the static
gates but cannot pass the harness:

  * semantic no-op        identical code on both sides (format-only change)
  * micro patch           < 3 changed lines — rarely enough to fix an issue
  * import hallucination  a new ``import``/``from ... import`` whose top-level
                          module does not exist in the checkout and is not
                          stdlib
  * rewrite risk          >=60% of a function body replaced (advisory gate
                          warning recorded at apply time or recomputed now)
  * off-localization      patch touches no file the localizer flagged
  * weak critic           critic score below 0.5

Output: ``results/patch_audit.json`` plus a printed summary and the
recommended re-solve set (flagged ids, weakest critic first).

Usage:
    python -m src.bench.audit_patches smoke50 smoke50-r1 smoke50-r2
    python -m src.bench.audit_patches smoke50 smoke50-r1 smoke50-r2 smoke50-r3
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RESULTS_DIR = ROOT / "results"

_IMPORT_RE = re.compile(
    r"^\s*(?:import\s+([A-Za-z_][A-Za-z0-9_.]*)|from\s+(\.[A-Za-z_][A-Za-z0-9_.]*|A-Za-z_)(?:[A-Za-z0-9_.]*)?\s+import)"
)


def merged_view(run_dirs: list[str]) -> dict[str, dict]:
    """Merge instance metas across run dirs; later dirs override earlier."""
    merged: dict[str, dict] = {}
    for tag, d in enumerate(run_dirs):
        run = RESULTS_DIR / d
        for meta_path in sorted(run.glob("*/meta.json")):
            try:
                m = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001 — keep scanning
                print(f"  [audit] unreadable meta {meta_path}: {exc}", file=sys.stderr)
                continue
            iid = m.get("instance_id") or meta_path.parent.name
            m["merged_run"] = d
            m["merged_path"] = str(meta_path)
            if iid not in merged or tag > _run_rank(merged[iid].get("merged_run"), run_dirs):
                merged[iid] = m
    return merged


def _run_rank(run: str | None, run_dirs: list[str]) -> int:
    try:
        return run_dirs.index(run)
    except ValueError:
        return -1


def load_patch(meta: dict) -> str:
    """Prefer the on-disk patch.diff next to meta; fall back to meta copy."""
    p = Path(meta["merged_path"]).parent / "patch.diff"
    if p.is_file():
        text = p.read_text(encoding="utf-8", errors="replace")
        if text.strip():
            return text
    return meta.get("model_patch") or ""


def new_imports(patch: str) -> list[str]:
    mods: list[str] = []
    for line in (patch or "").splitlines():
        if line.startswith("+++") or not line.startswith("+"):
            continue
        m = _IMPORT_RE.match(line[1:])
        if not m:
            continue
        name = (m.group(1) or m.group(2)).strip().split(".")[0]
        if name and name not in mods:
            mods.append(name)
    return mods


def module_exists(root: Path, name: str) -> bool:
    if name in sys.stdlib_module_names:
        return True
    return (root / name).is_dir() or (root / f"{name}.py").is_file()


def audit_instance(iid: str, meta: dict, checkout_roots: dict[str, Path]) -> dict:
    flags: list[str] = []
    patch = load_patch(meta)
    if not patch.strip():
        return {"instance_id": iid, "flags": ["no_patch"], "rescore": False}

    from src.bench.gates import changed_files, diff_stats, is_semantic_noop, rewrite_risk

    added, removed = diff_stats(patch)
    critic = meta.get("critic_score")

    if is_semantic_noop(patch):
        flags.append("semantic_noop")
    if added + removed < 3:
        flags.append("micro_patch")

    info_gates = (meta.get("patch_info") or {}).get("gates") or {}
    warnings = list(info_gates.get("warnings") or [])
    repo = checkout_roots.get(meta.get("repo", ""), None)
    if repo is None:
        repo = _checkout_for(iid)
    if repo is not None:
        for w in rewrite_risk(str(repo), patch):
            if not any("rewrite risk" in x for x in warnings):
                warnings.append(w)
        for name in new_imports(patch):
            if not module_exists(repo, name):
                flags.append(f"import_hallucination:{name}")

    loc = meta.get("localization") or {}
    loc_files = set()
    if isinstance(loc, dict):
        for key in ("file", "files", "primary_file", "candidate_files"):
            v = loc.get(key)
            if isinstance(v, str) and v:
                loc_files.add(v)
            elif isinstance(v, list):
                loc_files.update(str(x) for x in v)
    if not loc_files:
        loc_files = {meta.get("localization_file", "")}
        loc_files.discard("")
    touched = changed_files(patch)
    if loc_files and not any(
        f == lf or f.endswith("/" + lf.lstrip("/")) or lf in f for f in touched for lf in loc_files
    ):
        flags.append("off_localization")

    if critic is not None and critic < 0.5:
        flags.append(f"weak_critic:{critic:.2f}")

    return {
        "instance_id": iid,
        "flags": flags,
        "rescore": bool(flags),
        "critic": critic,
        "added": added,
        "removed": removed,
        "files": touched,
        "warnings": warnings,
        "run": meta.get("merged_run"),
        "failure_category": meta.get("failure_category"),
    }


def _checkout_for(iid: str) -> Path | None:
    try:
        from src.bench.checkout import checkout_path

        p = checkout_path(iid)
        return p if p.is_dir() else None
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit produced patches for loopholes")
    parser.add_argument("run_dirs", nargs="+", help="run dir names, weakest→strongest")
    parser.add_argument("--max-rescore", type=int, default=6,
                        help="cap the recommended re-solve list")
    parser.add_argument("--out", default=str(RESULTS_DIR / "patch_audit.json"))
    args = parser.parse_args()

    merged = merged_view(args.run_dirs)
    rows = []
    for iid, meta in sorted(merged.items()):
        cat = meta.get("failure_category")
        if cat not in (None, "ok") and cat:
            rows.append({
                "instance_id": iid, "flags": [f"red:{cat}"],
                "rescore": True, "critic": meta.get("critic_score"),
                "run": meta.get("merged_run"), "failure_category": cat,
            })
            continue
        rows.append(audit_instance(iid, meta, {}))

    flagged = [r for r in rows if r["rescore"]]
    rescore_ids = [
        r["instance_id"] for r in sorted(
            flagged, key=lambda r: (r["critic"] if r["critic"] is not None else 0)
        )
    ][: max(0, args.max_rescore)]

    out = {
        "run_dirs": args.run_dirs,
        "total": len(rows),
        "flagged": len(flagged),
        "rows": rows,
        "rescore_ids": rescore_ids,
    }
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[audit] {len(rows)} instances, {len(flagged)} flagged")
    for r in rows:
        if r["rescore"]:
            print(f"  FLAG {r['instance_id']}: {', '.join(r['flags'])} "
                  f"(critic={r.get('critic')})")
    print(f"[audit] recommended re-solve set: {rescore_ids}")
    print(f"[audit] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
