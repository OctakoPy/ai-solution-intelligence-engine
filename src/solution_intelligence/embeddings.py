"""Local embedding generation using sentence-transformers.

Uses a multilingual model so the demo requires no API key and no network
access. The multilingual model embeds English, Bahasa Malaysia, and Chinese
into a shared vector space, so queries in any supported language can match
against entries in any other.

Embeddings are persisted to a small on-disk cache keyed by the input text and
model. The synthetic dataset is static, so after one warm build every later
build (all dataset sizes and every server restart) loads cached vectors
instead of re-running the (slow) model on CPU.
"""

from __future__ import annotations

import hashlib
import json
import threading
from functools import lru_cache
from pathlib import Path

_MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"
_cache_lock = threading.Lock()

# Persist embeddings next to the dataset so they survive restarts. This file
# is reproducible from the static dataset and is not a generated artifact to
# commit; it is created lazily on first real ingestion.
_CACHE_PATH = Path(__file__).resolve().parents[2] / "data" / "embedding_cache.json"


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(_MODEL_NAME)


class LocalEmbedder:
    """Encodes text to vectors and computes cosine similarity.

    Encoded vectors are cached on disk (keyed by model + text) so repeated
    ingestion of the static demo dataset skips expensive model inference.
    """

    def __init__(self, model_name: str = _MODEL_NAME) -> None:
        self.model_name = model_name
        self._model = None
        self._cache: dict[str, list[float]] | None = None

    def _ensure_model(self):
        if self._model is None:
            with _cache_lock:
                if self._model is None:
                    self._model = _get_model()
        return self._model

    @staticmethod
    def _cache_key(text: str, for_query: bool) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"{_MODEL_NAME}::{('q' if for_query else 'd')}::{digest}"

    def _load_cache(self) -> dict[str, list[float]]:
        if self._cache is None:
            self._cache = {}
            if _CACHE_PATH.exists():
                try:
                    with _CACHE_PATH.open(encoding="utf-8") as f:
                        data = json.load(f)
                    self._cache = {k: list(v) for k, v in data.items()}
                except (OSError, ValueError):
                    self._cache = {}
        return self._cache

    def _save_cache(self) -> None:
        try:
            _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            tmp = _CACHE_PATH.with_suffix(".tmp")
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(self._cache, f)
            tmp.replace(_CACHE_PATH)
        except (OSError, TypeError):
            # Cache is a best-effort optimisation; never fail the caller.
            pass

    def _encode(self, texts: list[str], for_query: bool) -> list[list[float]]:
        cache = self._load_cache()
        keys = [self._cache_key(t, for_query) for t in texts]
        missing = [i for i, k in enumerate(keys) if k not in cache]
        if missing:
            model = self._ensure_model()
            batch = [texts[i] for i in missing]
            try:
                if for_query:
                    vecs = model.encode(
                        batch, normalize_embeddings=True, prompt_name="query"
                    )
                else:
                    vecs = model.encode(batch, normalize_embeddings=True)
            except TypeError:
                vecs = model.encode(batch, normalize_embeddings=True)
            for pos, vec in zip(missing, vecs):
                cache[keys[pos]] = [float(x) for x in vec.tolist()]
            self._save_cache()
        return [cache[k] for k in keys]

    def embed(self, text: str, for_query: bool = False) -> list[float]:
        """Return the embedding vector for a single piece of text."""
        return self._encode([text], for_query)[0]

    def similarity(self, a: list[float], b: list[float]) -> float:
        """Cosine similarity between two (already normalised) vectors."""
        if len(a) != len(b):
            raise ValueError("embedding dimensions do not match")
        dot = sum(x * y for x, y in zip(a, b))
        return max(0.0, min(1.0, dot))

    @staticmethod
    def dims() -> int:
        """Number of dimensions produced by the model."""
        return 1024
