"""
Encoders de embeddings para RAG.

FastEmbed (ONNX) sustituye a sentence-transformers + transformers + torch:
misma calidad para un corpus médico pequeño, ~90 MB vs ~2 GB.
HashEncoder es determinista y no descarga nada (tests / fallback).
"""

from __future__ import annotations

import hashlib
import logging
import math
import re
from typing import Protocol

logger = logging.getLogger(__name__)

_TOKEN = re.compile(r"[a-záéíóúñü0-9]+", re.IGNORECASE)


class EmbeddingEncoder(Protocol):
    dimension: int

    def encode(self, texts: list[str]) -> list[list[float]]: ...

    def encode_one(self, text: str) -> list[float]: ...


class HashEncoder:
    """Bag-of-words hasheado. Suficiente para tests y degradación sin modelo."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def encode(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def encode_one(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dimension
        for token in _TOKEN.findall(text.lower()):
            digest = hashlib.md5(token.encode("utf-8")).hexdigest()
            hashed = int(digest, 16)
            vec[hashed % self.dimension] += 1.0
            vec[(hashed // self.dimension) % self.dimension] += 0.5
        norm = math.sqrt(sum(value * value for value in vec)) or 1.0
        return [value / norm for value in vec]


class FastEmbedEncoder:
    """MiniLM multilingüe vía ONNX Runtime. No requiere PyTorch."""

    def __init__(self, model_name: str, cache_dir: str, dimension: int = 384):
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.dimension = dimension
        self._model = None

    def _load(self) -> None:
        if self._model is not None:
            return
        from pathlib import Path

        from fastembed import TextEmbedding

        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        logger.info("Cargando FastEmbed %s (cache=%s)", self.model_name, self.cache_dir)
        self._model = TextEmbedding(
            model_name=self.model_name,
            cache_dir=self.cache_dir,
        )

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        self._load()
        return [vector.tolist() for vector in self._model.embed(texts)]

    def encode_one(self, text: str) -> list[float]:
        encoded = self.encode([text])
        return encoded[0] if encoded else [0.0] * self.dimension


def build_encoder(settings) -> EmbeddingEncoder:
    backend = (settings.embedding_backend or "fastembed").lower()
    if backend == "hash":
        logger.info("Usando HashEncoder (%s dims) — sin descarga de modelo", settings.embedding_dimension)
        return HashEncoder(dimension=settings.embedding_dimension)

    return FastEmbedEncoder(
        model_name=settings.embedding_model,
        cache_dir=settings.embedding_cache_dir,
        dimension=settings.embedding_dimension,
    )
