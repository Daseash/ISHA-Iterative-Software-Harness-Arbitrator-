"""
ISHA Repo Context — Assembles the planner's view of the target repo.

Combines the compact tree-sitter AST map with RAG retrieval hits so the
planner sees structure first and only the most relevant source chunks.
"""

from src.ingestion.parser import RepoParser
from src.rag.indexer import QdrantIndexer
from src.rag.retriever import CodeRetriever
from src.tools.ast_mapper import ASTMapper
from src.tools.dependency_graph import DependencyGraph

MAX_CONTEXT_CHARS = 5500


def build_repo_context(issue_text: str, repo_path: str, top_k: int = 4) -> str:
    """Return AST MAP + IMPACT ANALYSIS + RELEVANT SNIPPETS text for the planner prompt."""
    repo_map = ASTMapper().build_map(repo_path)
    chunks = RepoParser().parse(repo_path)

    # Dependency graph & impact analysis
    dep_graph = DependencyGraph(repo_path)
    import re
    tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", issue_text))
    # Filter candidates against known symbols and files in dep_graph
    entry_points = [
        sym.name for sym in dep_graph.definitions if sym.name in tokens
    ]
    for f in dep_graph.files:
        stem = f.split("/")[-1].replace(".py", "")
        if stem in tokens:
            entry_points.append(f)
    if not entry_points:
        entry_points = [t for t in tokens if len(t) > 3][:5]

    impact = dep_graph.analyze_impact(entry_points)
    impact_report = dep_graph.render_impact_report(impact)

    snippets = []
    if chunks:
        indexer = QdrantIndexer()
        indexer.index(chunks)
        hits = CodeRetriever(chunks=chunks).search(issue_text, top_k=top_k)
        seen = set()
        for hit in hits:
            key = (hit.get("file_path"), hit.get("name"))
            if key in seen:
                continue
            seen.add(key)
            content = hit.get("content", "").strip()
            if content:
                snippets.append(
                    f"# {hit.get('file_path')} :: {hit.get('name')} "
                    f"(score {hit.get('score', 0):.3f})\n{content}"
                )

    sections = []
    if repo_map:
        sections.append(f"AST MAP:\n{repo_map}")
    if impact_report:
        sections.append(impact_report)
    if snippets:
        sections.append("RELEVANT SNIPPETS:\n" + "\n\n".join(snippets))

    context = "\n\n".join(sections)
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n...[truncated]"
    return context
