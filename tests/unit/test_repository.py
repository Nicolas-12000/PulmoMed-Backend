"""
Unit Tests - Repository Layer
Prueba índice en memoria + HashEncoder (sin descargar modelos)
"""

import pytest

from app.rag.embeddings import HashEncoder
from app.repositories.medical_knowledge_repo import MedicalKnowledgeRepository


@pytest.fixture
def repository():
    repo = MedicalKnowledgeRepository(encoder=HashEncoder(dimension=384))
    repo.initialize()
    return repo


class TestMedicalKnowledgeRepository:
    """Tests para Repository Layer"""

    def test_repository_initialization(self, repository):
        assert repository.encoder is not None
        assert repository.get_collection_stats()["count"] == 0

    @pytest.mark.asyncio
    async def test_hydrate_skipped_for_memory_backend(self, repository):
        assert await repository.hydrate_from_postgres() is False

    @pytest.mark.asyncio
    async def test_persist_skipped_when_empty(self, repository, monkeypatch):
        monkeypatch.setattr(repository.settings, "vector_backend", "pgvector")
        assert await repository.persist_to_postgres() is False

    @pytest.mark.asyncio
    async def test_hydrate_handles_db_errors(self, repository, monkeypatch):
        monkeypatch.setattr(repository.settings, "vector_backend", "pgvector")

        def boom():
            raise RuntimeError("db down")

        monkeypatch.setattr("app.core.database.get_session_factory", boom)
        assert await repository.hydrate_from_postgres() is False

    def test_add_documents(self, repository):
        texts = [
            "El cáncer de pulmón no microcítico representa el 85% de los casos.",
            "La mutación EGFR es común en adenocarcinomas de pacientes no fumadores.",
        ]
        metadatas = [
            {"source": "test_doc_1.pdf", "page": 1},
            {"source": "test_doc_2.pdf", "page": 2},
        ]
        ids = ["test_1", "test_2"]

        repository.add_documents(texts, metadatas, ids)

        stats = repository.get_collection_stats()
        assert stats["count"] == 2

    def test_retrieve_relevant_chunks(self, repository):
        texts = [
            "El tratamiento estándar para estadio IA es la resección quirúrgica.",
            "La quimioterapia con cisplatino mejora la supervivencia en estadio III.",
            "La inmunoterapia con pembrolizumab es efectiva en PD-L1 alto.",
        ]
        metadatas = [
            {"source": "test1.txt", "page": 1},
            {"source": "test2.txt", "page": 2},
            {"source": "test3.txt", "page": 3},
        ]
        repository.add_documents(texts, metadatas=metadatas)

        chunks = repository.retrieve_relevant_chunks(
            query="tratamiento quirúrgico estadio temprano", top_k=2
        )

        assert len(chunks) > 0
        assert len(chunks) <= 2
        assert "text" in chunks[0]
        assert "metadata" in chunks[0]
        assert "distance" in chunks[0]

    def test_get_collection_stats(self, repository):
        stats = repository.get_collection_stats()

        assert "status" in stats
        assert "count" in stats
        assert stats["status"] in ["empty", "active"]
        assert stats["count"] == 0

    def test_retrieve_empty_collection(self):
        repo = MedicalKnowledgeRepository(encoder=HashEncoder())
        repo.initialize()
        chunks = repo.retrieve_relevant_chunks("test query")
        assert chunks == []

    def test_initialize_is_idempotent_and_skips_empty_add(self, repository):
        repository.initialize()
        repository.add_documents([])
        repository.close()
        assert repository.get_collection_stats()["count"] == 0

    def test_lazy_hash_encoder_from_settings(self):
        repo = MedicalKnowledgeRepository()
        assert repo.encoder.dimension == 384

    @pytest.mark.asyncio
    async def test_hydrate_and_persist_with_fake_session(self, repository, monkeypatch):
        monkeypatch.setattr(repository.settings, "vector_backend", "pgvector")

        class FakeRow:
            id = "chunk-1"
            content = "Adenocarcinoma EGFR estadio IA"
            embedding = [0.1] * 32
            extra_metadata = {"source": "nccn"}
            source = "nccn"
            page = 1

        class FakeResult:
            def scalars(self):
                return self

            def all(self):
                return [FakeRow()]

        class FakeSession:
            merged = []

            async def execute(self, *_args, **_kwargs):
                return FakeResult()

            async def merge(self, obj):
                self.merged.append(obj)
                return obj

            async def commit(self):
                return None

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

        def factory():
            return FakeSession()

        monkeypatch.setattr(
            "app.core.database.get_session_factory",
            lambda: factory,
        )
        encoder = HashEncoder(dimension=32)
        repo = MedicalKnowledgeRepository(encoder=encoder)
        repo.settings.vector_backend = "pgvector"
        assert await repo.hydrate_from_postgres() is True
        assert repo.get_collection_stats()["count"] == 1
        assert await repo.persist_to_postgres() is True
