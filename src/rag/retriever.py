"""
ISHA Code Retriever — Hybrid search over indexed codebase.

Queries Qdrant when a server is available and falls back to local
lexical ranking over the parsed chunks so testing works without Docker.
"""

import os
import re

from src.rag.indexer import DEFAULT_COLLECTION, cosine, embed_text

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]+")


class CodeRetriever:
    """Search indexed code chunks by query."""

    def __init__(self, chunks=None, url: str | None = None, collection_name: str | None = None):
        self._chunks = list(chunks or [])
        self.url = url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.collection_name = collection_name or DEFAULT_COLLECTION

    def search(self, query: str, top_k: int = 5) -> list:
        """Return the top-k matching code chunks with scores."""
        if not query.strip():
            return []

        remote = self._search_qdrant(query, top_k)
        if remote is not None:
            return remote
        return self._search_local(query, top_k)

    # ------------------------------------------------------------------ #

    def _search_qdrant(self, query: str, top_k: int) -> list | None:
        if not self._chunks and not self.collection_name:
            return None
        try:
            from qdrant_client import QdrantClient

            client = QdrantClient(url=self.url, timeout=2)
            hits = client.query_points(
                collection_name=self.collection_name,
                query=embed_text(query),
                limit=top_k,
                with_payload=True,
            ).points
            return [
                {**{k: v for k, v in (hit.payload or {}).items()}, "score": hit.score}
                for hit in hits
            ]
        except Exception:
            return None

    def _search_local(self, query: str, top_k: int) -> list:
        """Lexical fallback: rank chunks by token overlap + vector similarity."""
        query_tokens = set(t.lower() for t in _TOKEN_RE.findall(query))
        query_vec = embed_text(query)

        scored = []
        for chunk in self._chunks:
            haystack = (
                f"{chunk.get('file_path', '')} {chunk.get('name', '')} "
                f"{chunk.get('content', '')}"
            ).lower()
            chunk_tokens = set(_TOKEN_RE.findall(haystack))
            overlap = len(query_tokens & chunk_tokens)
            if query_tokens:
                overlap /= len(query_tokens)
            semantic = cosine(query_vec, embed_text(haystack))
            score = 0.7 * overlap + 0.3 * max(semantic, 0.0)
            if score > 0:
                scored.append({**chunk, "score": round(score, 4)})

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]
