"""
ISHA Localizer Evaluation — does the localizer put the gold file in the top-k?

This is a *measurement* stage: gold patches are read here, after the fact, only
to score retrieval.  Nothing in this module is reachable from the solver, and
no number it produces may be quoted without the ``results/loc_eval.json`` file
that backs it.

Reported metrics (all over the selected slice):

    hit@1 / hit@3 / hit@5 / hit@8   at least one gold-patched file in the top k
    MRR                             1 / rank of the first gold-patched file
    source-only hit@8               same, ignoring docs/tests hits (what the
                                    coder can actually edit)

Chunks are expensive to build (~15s per checkout), so they are cached under
``data/cache/chunks/`` keyed by instance id.
"""

from __future__ import annotations

import argparse
import gzip
import json
import pickle
import time
from pathlib import Path

from src.bench import dataset as ds
from src.bench.classify import gold_files, gold_symbols
from src.tools.localizer import localize

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "results"
CACHE_DIR = ROOT / "data" / "cache" / "chunks"

_TOP_K = (1, 3, 5, 8)


def _is_source(path: str) -> bool:
    p = path.replace("\\", "/").lower()
    parts = p.split("/")
    if p.endswith((".py", ".pyx", ".pyi")):
        if any(seg in {"docs", "doc", "examples", "example", "benchmarks",
                       "tools", "scripts", "news", "debian"} for seg in parts[:-1]):
            return False
        if "tests" in parts or parts[-1].startswith("test_") or parts[-1].endswith("_test.py"):
            return False
        return True
    return False


def _chunks_for(record: dict, refresh: bool = False) -> list[dict]:
    from src.ingestion.parser import RepoParser

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = CACHE_DIR / f"{record['instance_id'].replace('/', '__')}.pkl.gz"
    if cache.is_file() and not refresh:
        with gzip.open(cache, "rb") as fh:
            return pickle.load(fh)
    chunks = RepoParser().parse(str(ROOT / "swebench_checkouts" /
                                    record["instance_id"].replace("/", "__")))
    with gzip.open(cache, "wb") as fh:
        pickle.dump(chunks, fh, protocol=pickle.HIGHEST_PROTOCOL)
    return chunks


def evaluate(limit: int = 30, mode: str = "dev", top_k: int = 8,
             refresh: bool = False, verbose: bool = True) -> dict:
    from src.bench.checkout import ensure_all

    records = ds.select_slice(ds.load_records(), limit=limit, mode=mode)
    if verbose:
        print(f"[loc_eval] preparing checkouts for {len(records)} instances ({mode}) ...")
    ensure_all(records)

    rows = []
    hits = {k: 0 for k in _TOP_K}
    func_hits = {k: 0 for k in _TOP_K}
    source_hits = {k: 0 for k in _TOP_K}
    rr_sum = 0.0
    func_rr_sum = 0.0
    started = time.time()

    for n, record in enumerate(records, 1):
        iid = record["instance_id"]
        expected = gold_files(record)
        expected_syms = gold_symbols(record)
        if not expected:
            continue
        checkout = ROOT / "swebench_checkouts" / iid.replace("/", "__")
        if not checkout.is_dir():
            rows.append({"instance_id": iid, "missing_checkout": True})
            continue
        try:
            chunks = _chunks_for(record, refresh=refresh)
            ranked = localize(record["problem_statement"], str(checkout),
                              top_k=top_k, chunks=chunks)
        except Exception as exc:  # keep the sweep going
            rows.append({"instance_id": iid, "error": f"{exc.__class__.__name__}: {exc}"})
            continue

        files = [c.file for c in ranked]
        rank = next((i + 1 for i, f in enumerate(files) if f in expected), 0)
        rr = 1.0 / rank if rank else 0.0
        rr_sum += rr
        for k in hits:
            if rank and rank <= k:
                hits[k] += 1

        func_rank = 0
        if expected_syms:
            func_rank = next(
                (i + 1 for i, c in enumerate(ranked)
                 if any(
                     s == sym or s in sym
                     for sym in ([c.symbol.split("::")[-1]] + getattr(c, "symbols", []))
                     for s in expected_syms
                     if s and sym
                 )), 0
            )
        func_rr = 1.0 / func_rank if func_rank else 0.0
        func_rr_sum += func_rr
        for k in func_hits:
            if func_rank and func_rank <= k:
                func_hits[k] += 1

        source_rank = next(
            (i + 1 for i, f in enumerate(files)
             if f in expected and _is_source(f)), 0
        )
        for k in source_hits:
            if source_rank and source_rank <= k:
                source_hits[k] += 1
        row = {
            "instance_id": iid,
            "rank": rank or None,
            "func_rank": func_rank or None,
            "source_rank": source_rank or None,
            "top": files[:top_k],
            "top_symbols": [c.symbol for c in ranked if c.symbol][:top_k],
            "expected_files": sorted(expected),
            "expected_symbols": sorted(expected_syms),
            "in_top8": bool(rank and rank <= 8),
        }
        rows.append(row)
        if verbose:
            mark = "OK " if rank and rank <= 8 else "MISS"
            fmark = f" fn_rank={func_rank or '-'}" if expected_syms else ""
            print(f"[{n}/{len(records)}] {mark} {iid}: rank={rank or '-'}"
                  f"{fmark} src_rank={source_rank or '-'} top={files[:2]}")

    scored = [r for r in rows if "rank" in r]
    n = len(scored) or 1
    sym_scored = [r for r in rows if r.get("expected_symbols")]
    n_sym = len(sym_scored) or 1

    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "limit": limit,
        "mode": mode,
        "top_k": top_k,
        "scored": len(scored),
        "skipped": len(rows) - len(scored),
        "hit_rates": {f"hit@{k}": round(hits[k] / n, 4) for k in _TOP_K},
        "function_hit_rates": {f"func_hit@{k}": round(func_hits[k] / n_sym, 4) for k in _TOP_K},
        "source_hit_rates": {f"hit@{k}": round(source_hits[k] / n, 4) for k in _TOP_K},
        "mrr": round(rr_sum / n, 4),
        "func_mrr": round(func_rr_sum / n_sym, 4),
        "elapsed_s": round(time.time() - started, 1),
        "rows": rows,
    }
    return payload


def render(payload: dict) -> str:
    lines = [
        f"### Localizer evaluation ({payload['mode']} {payload['limit']}, "
        f"{payload['scored']} scored / {payload['skipped']} skipped)",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| MRR (file) | {payload['mrr']:.3f} |",
    ]
    for k in _TOP_K:
        lines.append(f"| file hit@{k} | {payload['hit_rates'][f'hit@{k}']:.1%} |")
    lines.append("")
    lines.append("| Metric (function-level recall) | Value |")
    lines.append("|---|---|")
    lines.append(f"| MRR (function) | {payload.get('func_mrr', 0.0):.3f} |")
    for k in _TOP_K:
        lines.append(f"| func hit@{k} | {payload.get('function_hit_rates', {}).get(f'func_hit@{k}', 0.0):.1%} |")
    lines.append("")
    lines.append("| Metric (source files only) | Value |")
    lines.append("|---|---|")
    for k in _TOP_K:
        lines.append(f"| source hit@{k} | {payload['source_hit_rates'][f'hit@{k}']:.1%} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Score the localizer against gold patches")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--mode", default="dev", choices=["dev", "final", "train", "head", "stratified", "ids"])
    parser.add_argument("--slice", dest="mode", help="alias for --mode")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--refresh", action="store_true", help="rebuild the chunk cache")
    parser.add_argument("-o", "--out", default="", help="write the payload to this path")
    parser.add_argument("-q", "--quiet", action="store_true")
    args = parser.parse_args()

    payload = evaluate(limit=args.limit, mode=args.mode, top_k=args.top_k,
                       refresh=args.refresh, verbose=not args.quiet)
    out = Path(args.out) if args.out else RESULTS_DIR / "loc_eval.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(render(payload))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
