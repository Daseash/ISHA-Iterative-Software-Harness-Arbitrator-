"""Rebuild the loc reranker dataset without the patch-preview label artifact.

The v1 corpus put the *gold fix diff* on the positive side and the literal
string ``(file untouched by the fix)`` on every negative.  A cross-encoder
trivially learns that marker and scores every file with a diff as 1.0, which
makes it useless before a patch exists.

v2 keeps only the **pre-fix** side of the row's own file (context + removed
lines, never ``+`` fix lines) and pairs each negative path with real code from
the same repository, so the only learnable signal is issue <-> code relevance.

Usage:
    python scripts/rebuild_loc_dataset.py \
        --src dataset_build_clean/loc_reranker_train.jsonl \
        --out dataset_build_clean/loc_reranker_train_v2.jsonl
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import re
from pathlib import Path

_FILE_RE = re.compile(r"^FILE:\s*(.+?)\s*$", re.M)
_DIFF_RE = re.compile(r"^diff --git a/(.+?) b/(.+?)$", re.M)
_MAX_CODE_CHARS = 900
_CODE_HINTS = (
    "def ", "class ", "return ", "if ", "for ", "while ", "try:", "except",
    "raise ", "self.", "import ", "with ", "yield ", "assert ", "lambda ",
)


def _repo_of(instance_id: str) -> str:
    return instance_id.split("__")[0] if "__" in instance_id else instance_id


def _own_block(preview: str, target: str) -> str:
    """Return the diff block whose a/ or b/ path matches ``target``."""
    matches = list(_DIFF_RE.finditer(preview))
    for i, m in enumerate(matches):
        a_path, b_path = m.group(1), m.group(2)
        if a_path == target or b_path == target or a_path.endswith(target) or b_path.endswith(target):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(preview)
            return preview[m.end():end]
    return ""


def _dedupe(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        key = line.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(line)
    return out


def _snippet(block: str) -> tuple[str, int]:
    """Pre-fix code lines (context + removed), plus a rough quality score."""
    kept: list[str] = []
    changed = 0
    for line in block.splitlines():
        if line.startswith(("index ", "--- ", "+++ ", "@@", "\\")):
            continue
        if line.startswith("+") and not line.startswith("+++"):
            continue
        if line.startswith((" ", "-")):
            text = line[1:].rstrip()
            if not text.strip() or text.lstrip().startswith("#"):
                continue
            kept.append(text)
            if line.startswith("-"):
                changed += 1
    kept = _dedupe(kept)
    code = "\n".join(kept).strip()[:_MAX_CODE_CHARS]
    quality = sum(1 for line in code.splitlines() if any(h in line for h in _CODE_HINTS))
    quality += min(changed, 5)
    return code, quality


def _substantive(block: str) -> bool:
    changed = [
        line[1:] for line in block.splitlines()
        if line.startswith("-") and not line.startswith("---")
    ]
    if not changed:
        return False
    codey = sum(1 for line in changed if any(h in line for h in _CODE_HINTS))
    return codey >= 1 or len(changed) >= 3


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="dataset_build_clean/loc_reranker_train.jsonl")
    ap.add_argument("--out", default="dataset_build_clean/loc_reranker_train_v2.jsonl")
    ap.add_argument("--negatives-per-instance", type=int, default=3)
    ap.add_argument("--min-quality", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    rows: list[dict] = []
    repo_code: dict[str, dict[str, tuple[str, int]]] = collections.defaultdict(dict)

    with open(args.src, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            m = _FILE_RE.search(row.get("sentence2", ""))
            if not m:
                continue
            path = m.group(1).strip()
            block = _own_block(row.get("sentence2", ""), path)
            code, quality = _snippet(block)
            repo = _repo_of(row["instance_id"])
            row.update({"_path": path, "_repo": repo, "_code": code,
                        "_quality": quality, "_substantive": _substantive(block)})
            rows.append(row)
            if quality > repo_code[repo].get(path, ("", -1))[1]:
                repo_code[repo][path] = (code, quality)

    by_instance: dict[str, dict[str, list[dict]]] = collections.defaultdict(
        lambda: {"pos": [], "neg": []}
    )
    for row in rows:
        key = "pos" if row.get("label") == 1.0 else "neg"
        by_instance[row["instance_id"]][key].append(row)

    written = 0
    kept_instances = 0
    with open(args.out, "w", encoding="utf-8", newline="\n") as out:
        for iid, groups in by_instance.items():
            repo = _repo_of(iid)
            code = {p: c for p, (c, q) in repo_code.get(repo, {}).items()
                    if q >= args.min_quality}
            pos_rows = [
                r for r in groups["pos"]
                if r["_quality"] >= args.min_quality and r["_substantive"]
            ]
            if not pos_rows or not code:
                continue
            pos_paths = {r["_path"] for r in pos_rows}
            neg_pool = [(p, c) for p, c in code.items() if p not in pos_paths]
            if not neg_pool:
                continue
            rng.shuffle(neg_pool)
            neg_rows = neg_pool[: args.negatives_per_instance * len(pos_rows)]
            issue = pos_rows[0]["sentence1"]
            for row in pos_rows:
                out.write(json.dumps({
                    "instance_id": iid,
                    "sentence1": row["sentence1"],
                    "sentence2": f"FILE: {row['_path']}\nCODE:\n{row['_code']}",
                    "label": 1.0,
                }, ensure_ascii=False) + "\n")
                written += 1
            for path, snippet in neg_rows:
                out.write(json.dumps({
                    "instance_id": iid,
                    "sentence1": issue,
                    "sentence2": f"FILE: {path}\nCODE:\n{snippet}",
                    "label": 0.0,
                }, ensure_ascii=False) + "\n")
                written += 1
            kept_instances += 1

    print(f"[loc-v2] instances={kept_instances} rows={written} -> {args.out}")
    size = Path(args.out).stat().st_size / 1e6
    print(f"[loc-v2] size={size:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
