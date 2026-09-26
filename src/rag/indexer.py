"""
ISHA Qdrant Indexer — Vectorizes repo chunks for hybrid retrieval.

Uses a deterministic, dependency-free 384-dim hashing embedder so the
pipeline works offline with no GPU or model download. When a Qdrant
server is reachable (Docker or Qdrant Cloud) the vectors are pushed
there; otherwise chunks stay in a local store the retriever can read.
"""

import hashlib
import math
import os
import re
from collections import Counter

VECTOR_SIZE = 384
DEFAULT_COLLECTION = "isha_codebase"

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+")


def embed_text(text: str, dim: int = VECTOR_SIZE) -> list:
    """Deterministic bag-of-tokens hashing embedder (unit-normalized)."""
    vec = [0.0] * dim
    tokens = _TOKEN_RE.findall(text.lower())
    if not tokens:
        return vec
    for token, count in Counter(tokens).items():
        digest = hashlib.sha1(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "little") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vec[idx] += sign * (1.0 + math.log(count))
    norm = math.sqrt(sum(v * v for v in vec))
    if norm:
        vec = [v / norm for v in vec]
    return vec


def cosine(a: list, b: list) -> float:
    """Cosine similarity between two equal-length vectors."""
    return sum(x * y for x, y in zip(a, b))


class QdrantIndexer:
    """Index code chunks into Qdrant for hybrid search."""

    def __init__(self, url: str | None = None, api_key: str | None = None):
        self.url = url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")
        self.chunks: list[dict] = []
        self.online = False
        self.collection_name = DEFAULT_COLLECTION

    def index(self, chunks: list, collection_name: str = DEFAULT_COLLECTION) -> dict:
        """Push chunks to Qdrant (or keep them locally if no server)."""
        self.chunks = list(chunks or [])
        self.collection_name = collection_name

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, PointStruct, VectorParams

            client = QdrantClient(url=self.url, api_key=self.api_key, timeout=2)
            client.recreate_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            points = []
            for i, chunk in enumerate(self.chunks):
                points.append(
                    PointStruct(
                        id=i,
                        vector=embed_text(
                            f"{chunk.get('file_path', '')} {chunk.get('name', '')} "
                            f"{chunk.get('content', '')}"
                        ),
                        payload={**chunk, "chunk_id": i},
                    )
                )
            if points:
                client.upsert(collection_name=collection_name, points=points)
            self.online = True
            return {"mode": "qdrant", "collection": collection_name, "count": len(points)}
        except Exception as exc:
            self.online = False
            return {
                "mode": "local",
                "collection": collection_name,
                "count": len(self.chunks),
                "detail": f"Qdrant unavailable ({exc.__class__.__name__}); using local store",
            }
