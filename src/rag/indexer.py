"""
ISHA Qdrant Indexer — Indexes repo chunks with hybrid vector + BM25.

Implemented in Phase 2.
"""


class QdrantIndexer:
    """Index code chunks into Qdrant for hybrid search."""

    def index(self, chunks: list, collection_name: str = "isha_codebase"):
        """Push chunks to Qdrant with dense + sparse vectors."""
        # TODO: Implement in Phase 2
        pass
