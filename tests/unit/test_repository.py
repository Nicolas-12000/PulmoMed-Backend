"""
Unit Tests - Repository Layer
Prueba acceso a ChromaDB y retrieval
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from app.repositories.medical_knowledge_repo import MedicalKnowledgeRepository
from app.core.config import get_settings


@pytest.fixture
def temp_chroma_dir():
    """Fixture: Directorio temporal para ChromaDB (aislamiento entre tests)"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup después del test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def repository(temp_chroma_dir, monkeypatch):
    """Fixture: Repositorio con colección temporal"""
    # Parchear settings para usar directorio temporal
    settings = get_settings()
    monkeypatch.setattr(settings, "chroma_persist_dir", temp_chroma_dir)
    
    repo = MedicalKnowledgeRepository()
    repo.settings.chroma_persist_dir = temp_chroma_dir
    repo.initialize()
    return repo


class TestMedicalKnowledgeRepository:
    """Tests para Repository Layer"""
    
    def test_repository_initialization(self, repository):
        """Test: Inicialización correcta del repositorio"""
        assert repository._client is not None
        assert repository._embedding_model is not None
    
    def test_add_documents(self, repository):
        """Test: Añadir documentos a la colección"""
        texts = [
            "El cáncer de pulmón no microcítico representa el 85% de los casos.",
            "La mutación EGFR es común en adenocarcinomas de pacientes no fumadores."
        ]
        metadatas = [
            {"source": "test_doc_1.pdf", "page": 1},
            {"source": "test_doc_2.pdf", "page": 2}
        ]
        ids = ["test_1", "test_2"]
        
        repository.add_documents(texts, metadatas, ids)
        
        stats = repository.get_collection_stats()
        assert stats["count"] == 2
    
    def test_retrieve_relevant_chunks(self, repository):
        """Test: Retrieval de chunks relevantes"""
        # Primero añadir documentos
        texts = [
            "El tratamiento estándar para estadio IA es la resección quirúrgica.",
            "La quimioterapia con cisplatino mejora la supervivencia en estadio III.",
            "La inmunoterapia con pembrolizumab es efectiva en PD-L1 alto."
        ]
        repository.add_documents(texts)
        
        # Query relevante
        chunks = repository.retrieve_relevant_chunks(
            query="tratamiento quirúrgico estadio temprano",
            top_k=2
        )
        
        assert len(chunks) > 0
        assert len(chunks) <= 2
        assert "text" in chunks[0]
        assert "metadata" in chunks[0]
        assert "distance" in chunks[0]
    
    def test_get_collection_stats(self, repository):
        """Test: Obtener estadísticas de la colección"""
        stats = repository.get_collection_stats()
        
        assert "status" in stats
        assert "count" in stats
        assert stats["status"] in ["empty", "active"]
        assert stats["count"] == 0  # Colección nueva vacía
    
    def test_retrieve_empty_collection(self, temp_chroma_dir, monkeypatch):
        """Test: Retrieval en colección vacía no debe fallar"""
        settings = get_settings()
        monkeypatch.setattr(settings, "chroma_persist_dir", temp_chroma_dir)
        
        repo = MedicalKnowledgeRepository()
        repo.settings.chroma_persist_dir = temp_chroma_dir
        repo.initialize()
        
        chunks = repo.retrieve_relevant_chunks("test query")
        assert chunks == []
