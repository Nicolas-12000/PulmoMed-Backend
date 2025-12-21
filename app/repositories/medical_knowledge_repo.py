"""
Medical Knowledge Repository - ChromaDB Abstraction
Repository Pattern: Abstrae acceso a vector database (SOLID: OCP)
"""

import logging
from typing import Dict, List

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class MedicalKnowledgeRepository:
    """
    Repositorio para conocimiento médico vectorizado
    Abstrae ChromaDB para facilitar cambio a Weaviate/Pinecone después
    """

    def __init__(self):
        self.settings = get_settings()
        self._client = None
        self._collection = None
        self._embedding_model = None

    def initialize(self):
        """
        Inicializa ChromaDB y modelo de embeddings
        Lazy loading: solo se carga cuando se necesita
        """
        if self._client is not None:
            return

        logger.info(f"Inicializando ChromaDB en {self.settings.chroma_persist_dir}")

        # ChromaDB client (persistente)
        self._client = chromadb.PersistentClient(
            path=self.settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Obtener o crear colección
        try:
            self._collection = self._client.get_collection(
                name=self.settings.collection_name
            )
            logger.info(f"Colección '{self.settings.collection_name}' cargada")
        except Exception:
            logger.warning("Colección no existe, se creará al indexar documentos")
            self._collection = None

        # Modelo de embeddings (BGE-base-en-v1.5)
        logger.info(f"Cargando modelo {self.settings.embedding_model}")
        self._embedding_model = SentenceTransformer(
            self.settings.embedding_model, device=self.settings.embedding_device
        )

    def retrieve_relevant_chunks(
        self, query: str, top_k: int | None = None
    ) -> List[Dict[str, any]]:
        """
        Recupera chunks relevantes para una consulta (RAG retrieval)

        Args:
            query: Consulta en lenguaje natural
            top_k: Número de chunks a recuperar (default: settings.retrieval_top_k)

        Returns:
            Lista de dicts con {text, metadata, distance}
        """
        if self._collection is None:
            logger.warning("Colección vacía, retornando lista vacía")
            return []

        top_k = top_k or self.settings.retrieval_top_k

        # Generar embedding de la consulta
        query_embedding = self._embedding_model.encode(
            query, convert_to_tensor=False
        ).tolist()

        # Query a ChromaDB
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        # Formatear resultados
        chunks = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                chunks.append(
                    {
                        "text": doc,
                        "metadata": (
                            results["metadatas"][0][i] if results["metadatas"] else {}
                        ),
                        "distance": (
                            results["distances"][0][i] if results["distances"] else 1.0
                        ),
                    }
                )

        logger.info(f"Recuperados {len(chunks)} chunks para query: '{query[:50]}...'")
        return chunks

    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict] | None = None,
        ids: List[str] | None = None,
    ):
        """
        Añade documentos a la colección (para futura indexación de PDFs)

        Args:
            texts: Lista de textos a indexar
            metadatas: Metadata asociada a cada texto
            ids: IDs únicos (si None, se autogenera)
        """
        if self._collection is None:
            self._collection = self._client.create_collection(
                name=self.settings.collection_name
            )

        # Generar embeddings
        embeddings = self._embedding_model.encode(
            texts, convert_to_tensor=False, show_progress_bar=True
        ).tolist()

        # Generar IDs si no se proporcionan
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(texts))]

        # Insertar en ChromaDB
        self._collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas or [{} for _ in texts],
            ids=ids,
        )

        logger.info(f"Añadidos {len(texts)} documentos a la colección")

    def get_collection_stats(self) -> Dict[str, any]:
        """Retorna estadísticas de la colección"""
        if self._collection is None:
            return {"status": "empty", "count": 0}

        return {
            "status": "active",
            "count": self._collection.count(),
            "name": self.settings.collection_name,
        }

    def close(self):
        """Cierra conexiones (cleanup)"""
        # ChromaDB se persiste automáticamente
        logger.info("Repository cerrado")


# Singleton global (Dependency Injection simple)
_repository_instance = None


def get_repository() -> MedicalKnowledgeRepository:
    """Factory para Dependency Injection"""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = MedicalKnowledgeRepository()
        _repository_instance.initialize()
    return _repository_instance
