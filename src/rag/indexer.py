"""
ISHA Qdrant Indexer — Vectorizes repo chunks for hybrid retrieval.

Primary: `all-MiniLM-L6-v2` (384d, semantic) when `ISHA_EMBEDDER=minilm` and
`sentence-transformers` is installed. Fallback: deterministic dependency-free
384-dim hashing embedder (offline, no GPU/model download). Same VECTOR_SIZE so
no migration is needed (P0-06).
"""

import hashlib
import math
import os
import re
from collections import Counter

VECTOR_SIZE = 384
DEFAULT_COLLECTION = "isha_codebase"

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+")

# P0-06: cache chunk/query vectors (was recomputed per-chunk in localizer).
_EMBED_CACHE: dict[tuple[str, int], list] = {}
_MINILM_MODEL = None
_MINILM_FAILED = False


def _minilm_embed(text: str, dim: int) -> list | None:
    """Return MiniLM vector or None (fallback to hashing). Lazy, cached model."""
    global _MINILM_MODEL, _MINILM_FAILED
    if _MINILM_FAILED or dim != VECTOR_SIZE:
        return None
    if os.getenv("ISHA_EMBEDDER", "hashing").lower() != "minilm":
        return None
    try:
        if _MINILM_MODEL is None:
            from sentence_transformers import SentenceTransformer

            _MINILM_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        vec = _MINILM_MODEL.encode(text or "", normalize_embeddings=True)
        return [float(x) for x in vec[:dim]]
    except Exception:
        _MINILM_FAILED = True
        return None


def embed_text(text: str, dim: int = VECTOR_SIZE) -> list:
    """Semantic (MiniLM when enabled) else deterministic hashing embedder."""
    key = (text or "", dim)
    hit = _EMBED_CACHE.get(key)
    if hit is not None:
        return list(hit)
    mini = _minilm_embed(text or "", dim)
    if mini is not None:
        _EMBED_CACHE[key] = mini
        return list(mini)
    vec = [0.0] * dim
    tokens = _TOKEN_RE.findall((text or "").lower())
    if tokens:
        for token, count in Counter(tokens).items():
            digest = hashlib.sha1(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "little") % dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[idx] += sign * (1.0 + math.log(count))
        norm = math.sqrt(sum(v * v for v in vec))
        if norm:
            vec = [v / norm for v in vec]
    _EMBED_CACHE[key] = vec
    return list(vec)


def clear_embed_cache() -> None:
    _EMBED_CACHE.clear()


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

            client = QdrantClient(url=self.url, api_key=self.api_key, timeout=2, check_compatibility=False)
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
