"""
ISHA Repo Context — Assembles the planner's view of the target repo.

Combines the compact tree-sitter AST map with RAG retrieval hits so the
planner sees structure first and only the most relevant source chunks.
"""

from src.ingestion.parser import RepoParser
from src.rag.indexer import QdrantIndexer
from src.rag.retriever import CodeRetriever
from src.tools.ast_mapper import ASTMapper

MAX_CONTEXT_CHARS = 4000


def build_repo_context(issue_text: str, repo_path: str, top_k: int = 4) -> str:
    """Return 'AST MAP' + 'RELEVANT SNIPPETS' text for the planner prompt."""
    repo_map = ASTMapper().build_map(repo_path)
    chunks = RepoParser().parse(repo_path)

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
    if snippets:
        sections.append("RELEVANT SNIPPETS:\n" + "\n\n".join(snippets))

    context = "\n\n".join(sections)
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n...[truncated]"
    return context
