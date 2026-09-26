"""
ISHA Code Retriever — Hybrid search over indexed codebase.

Falls back to simple string matching if Qdrant is not running.
Implemented in Phase 2.
"""


class CodeRetriever:
    """Search indexed code chunks by query."""

    def __init__(self, chunks=None):
        self._chunks = chunks or []

    def search(self, query: str, top_k: int = 5) -> list:
        """Return the top-k matching code chunks."""
        # TODO: Implement in Phase 2
        return []
