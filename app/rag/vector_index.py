"""Índice vectorial en RAM. pgvector persiste; las consultas VR se resuelven aquí."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class IndexedChunk:
    chunk_id: str
    text: str
    metadata: dict[str, Any]
    embedding: list[float]


@dataclass
class InMemoryVectorIndex:
    items: list[IndexedChunk] = field(default_factory=list)

    def clear(self) -> None:
        self.items.clear()

    @property
    def count(self) -> int:
        return len(self.items)

    def add(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        metadatas = metadatas or [{} for _ in texts]
        existing = {item.chunk_id: index for index, item in enumerate(self.items)}
        for chunk_id, text, embedding, metadata in zip(ids, texts, embeddings, metadatas):
            chunk = IndexedChunk(
                chunk_id=chunk_id,
                text=text,
                metadata=metadata or {},
                embedding=list(embedding),
            )
            if chunk_id in existing:
                self.items[existing[chunk_id]] = chunk
            else:
                self.items.append(chunk)

    def query(self, embedding: list[float], top_k: int) -> list[dict[str, Any]]:
        if not self.items or top_k <= 0:
            return []

        query = np.asarray(embedding, dtype=np.float64)
        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            return []

        scored: list[tuple[float, IndexedChunk]] = []
        for item in self.items:
            vector = np.asarray(item.embedding, dtype=np.float64)
            denom = query_norm * np.linalg.norm(vector)
            if denom == 0:
                distance = 1.0
            else:
                distance = 1.0 - float(np.dot(query, vector) / denom)
            scored.append((distance, item))

        scored.sort(key=lambda pair: pair[0])
        return [
            {
                "id": item.chunk_id,
                "text": item.text,
                "metadata": item.metadata,
                "distance": distance,
            }
            for distance, item in scored[:top_k]
        ]
