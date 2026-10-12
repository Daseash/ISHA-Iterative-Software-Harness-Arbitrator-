import json, re, sys, time
sys.path.insert(0, ".")
repo = r"C:\Users\Eashwar\ISHA\isha-agent\swebench_checkouts\sphinx-doc__sphinx-10451"
recs = json.load(open(r"data\swebench_lite.json", encoding="utf-8"))
r = [x for x in recs if x["instance_id"] == "sphinx-doc__sphinx-10451"][0]

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
