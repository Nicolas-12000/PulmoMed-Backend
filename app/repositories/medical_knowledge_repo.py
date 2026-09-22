"""
Medical Knowledge Repository
Consulta en RAM (latencia VR). PostgreSQL + pgvector es la fuente persistente.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select

from app.core.config import get_settings
from app.rag.embeddings import EmbeddingEncoder, build_encoder
from app.rag.vector_index import InMemoryVectorIndex

logger = logging.getLogger(__name__)


class MedicalKnowledgeRepository:
    """
    Repositorio de conocimiento médico.
    - retrieve/add son síncronos contra un índice en memoria.
    - hydrate/persist sincronizan con pgvector cuando PostgreSQL está disponible.
    """

    def __init__(self, encoder: EmbeddingEncoder | None = None):
        self.settings = get_settings()
        self._encoder = encoder
        self._index = InMemoryVectorIndex()
        self._initialized = False

    @property
    def encoder(self) -> EmbeddingEncoder:
        if self._encoder is None:
            self._encoder = build_encoder(self.settings)
        return self._encoder

    def initialize(self) -> None:
        if self._initialized:
            return
        logger.info(
            "RAG listo (backend=%s, embeddings=%s)",
            self.settings.vector_backend,
            self.settings.embedding_backend,
        )
        self._initialized = True

    def retrieve_relevant_chunks(
        self, query: str, top_k: int | None = None
    ) -> list[dict[str, Any]]:
        if self._index.count == 0:
            logger.warning("Colección vacía, retornando lista vacía")
            return []

        top_k = top_k or self.settings.retrieval_top_k
        query_embedding = self.encoder.encode_one(query)
        chunks = self._index.query(query_embedding, top_k)
        logger.info("Recuperados %s chunks para query: '%s...'", len(chunks), query[:50])
        return chunks

    def add_documents(
        self,
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        if not texts:
            return

        embeddings = self.encoder.encode(texts)
        if ids is None:
            ids = [f"doc_{self._index.count + i}" for i in range(len(texts))]

        self._index.add(
            ids=ids,
            texts=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info("Añadidos %s documentos al índice RAG", len(texts))

    def get_collection_stats(self) -> dict[str, Any]:
        count = self._index.count
        return {
            "status": "active" if count else "empty",
            "count": count,
            "name": self.settings.collection_name,
            "backend": self.settings.vector_backend,
            "embedding_backend": self.settings.embedding_backend,
        }

    async def hydrate_from_postgres(self) -> bool:
        if self.settings.vector_backend != "pgvector":
            return False

        try:
            from app.core.database import get_session_factory
            from app.models.db_models import MedicalChunk

            session_factory = get_session_factory()
            async with session_factory() as session:
                result = await session.execute(select(MedicalChunk))
                rows = result.scalars().all()
                if not rows:
                    return False

                self._index.clear()
                self._index.add(
                    ids=[row.id for row in rows],
                    texts=[row.content for row in rows],
                    embeddings=[list(row.embedding) for row in rows],
                    metadatas=[_row_metadata(row) for row in rows],
                )
                logger.info("Cargados %s chunks desde pgvector", len(rows))
                return True
        except Exception as exc:
            logger.warning("No se pudo hidratar pgvector (%s). RAG queda en memoria.", exc)
            return False

    async def persist_to_postgres(self) -> bool:
        if self.settings.vector_backend != "pgvector" or self._index.count == 0:
            return False

        try:
            from app.core.database import get_session_factory
            from app.models.db_models import MedicalChunk

            session_factory = get_session_factory()
            async with session_factory() as session:
                for item in self._index.items:
                    await session.merge(
                        MedicalChunk(
                            id=item.chunk_id,
                            content=item.text,
                            source=str(item.metadata.get("source", "")),
                            page=item.metadata.get("page"),
                            extra_metadata=item.metadata,
                            embedding=item.embedding,
                        )
                    )
                await session.commit()
            logger.info("Persistidos %s chunks en pgvector", self._index.count)
            return True
        except Exception as exc:
            logger.warning("No se pudo persistir en pgvector: %s", exc)
            return False

    def close(self) -> None:
        logger.info("Repository cerrado (%s documentos en RAM)", self._index.count)


def _row_metadata(row) -> dict[str, Any]:
    metadata = dict(row.extra_metadata or {})
    metadata.setdefault("source", row.source or "pgvector")
    if row.page is not None:
        metadata.setdefault("page", row.page)
    return metadata


_repository_instance: MedicalKnowledgeRepository | None = None


def get_repository() -> MedicalKnowledgeRepository:
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = MedicalKnowledgeRepository()
        _repository_instance.initialize()
    return _repository_instance


def reset_repository() -> None:
    global _repository_instance
    _repository_instance = None
