import argparse
import json, re, sys, time
from pathlib import Path

# P1-10: portable (was hardcoded C:\... + backslash paths, Windows-only).
ap = argparse.ArgumentParser(description="Time localizer pipeline stages")
ap.add_argument("--repo", default="swebench_checkouts/sphinx-doc__sphinx-10451")
ap.add_argument("--instance", default="sphinx-doc__sphinx-10451")
ap.add_argument("--data", default="data/swebench_lite.json")
args = ap.parse_args()

sys.path.insert(0, ".")
repo = str(Path(args.repo))
recs = json.load(open(Path(args.data), encoding="utf-8"))
r = [x for x in recs if x["instance_id"] == args.instance][0]

from src.tools.ast_mapper import ASTMapper
from src.ingestion.parser import RepoParser
from src.tools.dependency_graph import DependencyGraph
from src.rag.indexer import QdrantIndexer
from src.rag.retriever import CodeRetriever

t0 = time.time()
m = ASTMapper().build_map(repo)
print("ast_map %.1f" % (time.time() - t0), flush=True)
t0 = time.time()
ch = RepoParser().parse(repo)
print("parser %.1f chunks=%d" % (time.time() - t0, len(ch)), flush=True)
t0 = time.time()
dg = DependencyGraph(repo)
print("depgraph_init %.1f" % (time.time() - t0), flush=True)
toks = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", r["problem_statement"]))
eps = [s.name for s in dg.definitions if s.name in toks] or [t for t in toks if len(t) > 3][:5]
t0 = time.time()
imp = dg.analyze_impact(eps)
rep = dg.render_impact_report(imp)
print("impact %.1f" % (time.time() - t0), flush=True)
t0 = time.time()
ix = QdrantIndexer()
ix.index(ch)
print("qdrant_index %.1f" % (time.time() - t0), flush=True)
t0 = time.time()
hits = CodeRetriever(chunks=ch).search(r["problem_statement"], top_k=4)
print("retrieval %.1f" % (time.time() - t0), flush=True)
t0 = time.time()
from src.agents.context import build_repo_context
ctx = build_repo_context(r["problem_statement"], repo)
print("build_repo_context_total %.1f chars=%d" % (time.time() - t0, len(ctx)), flush=True)
