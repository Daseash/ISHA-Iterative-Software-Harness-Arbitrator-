"""
ISHA Qdrant Indexer — Vectorizes repo chunks for hybrid retrieval.

Primary: `BAAI/bge-small-en-v1.5` (384d, 512-token window, semantic code retrieval).
Secondary: `all-MiniLM-L6-v2` (384d, semantic fallback).
Fallback: deterministic dependency-free 384-dim SHA1 hashing embedder when
`sentence-transformers` is not installed (offline, no GPU/model download).
Isolated collections: Neural embeddings and SHA1 hashes are stored in separate
collections to prevent cross-vector space distortion (Subsystem 2 upgraded spec).
"""

import hashlib
import math
import os
import re
from collections import Counter

VECTOR_SIZE = 384
DEFAULT_COLLECTION = "isha_codebase"

PRIMARY_MODEL_NAME = os.getenv("ISHA_EMBEDDER_MODEL", "BAAI/bge-small-en-v1.5")
FALLBACK_MODEL_NAME = "all-MiniLM-L6-v2"

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+")

# Cache chunk/query vectors
_EMBED_CACHE: dict[tuple[str, int], list] = {}
_NEURAL_MODEL = None
_NEURAL_FAILED = False


def _neural_embed(text: str, dim: int) -> list | None:
    """Return BGE-small / MiniLM vector or None (fallback to hashing). Lazy, cached model."""
    global _NEURAL_MODEL, _NEURAL_FAILED
    if _NEURAL_FAILED or dim != VECTOR_SIZE:
        return None
    mode = os.getenv("ISHA_EMBEDDER", "neural").lower()
    if mode in ("sha1", "hash", "hashing", "offline"):
        return None
    try:
        if _NEURAL_MODEL is None:
            from sentence_transformers import SentenceTransformer

            try:
                _NEURAL_MODEL = SentenceTransformer(PRIMARY_MODEL_NAME)
            except Exception:
                _NEURAL_MODEL = SentenceTransformer(FALLBACK_MODEL_NAME)
        vec = _NEURAL_MODEL.encode(text or "", normalize_embeddings=True)
        return [float(x) for x in vec[:dim]]
    except Exception:
        _NEURAL_FAILED = True
        return None


def is_neural_active() -> bool:
    """Return True if neural embedding (BGE/MiniLM) is currently active."""
    global _NEURAL_FAILED
    if _NEURAL_FAILED:
        return False
    sample = _neural_embed("probe", VECTOR_SIZE)
    return sample is not None


def format_chunk_for_embedding(chunk: dict) -> str:
    """Prepend AST function/class context header to chunk before embedding."""
    file_path = chunk.get("file_path", "")
    name = chunk.get("name", "")
    content = str(chunk.get("content", "")).strip()
    return f"# File: {file_path} | Name: {name}\n{content}".strip()


def embed_text(text: str, dim: int = VECTOR_SIZE) -> list:
    """Semantic (BGE-small / MiniLM when enabled) else deterministic hashing embedder."""
    key = (text or "", dim)
    hit = _EMBED_CACHE.get(key)
    if hit is not None:
        return list(hit)
    neural = _neural_embed(text or "", dim)
    if neural is not None:
        _EMBED_CACHE[key] = neural
        return list(neural)
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
        """Push chunks to Qdrant with isolated neural vs sha1 collections."""
        self.chunks = list(chunks or [])
        # Subsystem 2: Separate collections by embedder type so vector spaces never collide
        neural_ok = is_neural_active()
        eff_collection = collection_name if neural_ok else f"{collection_name}_sha1"
        self.collection_name = eff_collection

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, PointStruct, VectorParams

            client = QdrantClient(url=self.url, api_key=self.api_key, timeout=2, check_compatibility=False)
            client.recreate_collection(
                collection_name=eff_collection,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            points = []
            for i, chunk in enumerate(self.chunks):
                text_to_embed = format_chunk_for_embedding(chunk)
                points.append(
                    PointStruct(
                        id=i,
                        vector=embed_text(text_to_embed),
                        payload={**chunk, "chunk_id": i},
                    )
                )
            if points:
                client.upsert(collection_name=eff_collection, points=points)
            self.online = True
            return {"mode": "qdrant", "collection": eff_collection, "count": len(points), "neural": neural_ok}
        except Exception as exc:
            self.online = False
            return {
                "mode": "local",
                "collection": eff_collection,
                "count": len(self.chunks),
                "detail": f"Qdrant unavailable ({exc.__class__.__name__}); using local store",
                "neural": neural_ok,
            }
