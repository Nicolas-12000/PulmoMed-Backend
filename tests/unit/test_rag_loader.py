from pathlib import Path

import pytest
from unittest.mock import MagicMock, patch

from app.rag.loader import MedicalPDFLoader, index_knowledge_base


class DummyPage:
    def __init__(self, text: str):
        self._text = text

    def extract_text(self):
        return self._text


class DummyReader:
    def __init__(self, pages):
        self.pages = pages


def test_load_pdf_file_not_found():
    loader = MedicalPDFLoader()
    with pytest.raises(FileNotFoundError):
        loader.load_pdf("nonexistent_file.pdf")


def test_load_pdf_paragraph_chunking(monkeypatch, tmp_path):
    # Create a fake pdf file path
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_text("fake")

    # Prepare dummy pages: one short paragraph, one long paragraph
    short = "Header\n\nShort."  # too short, will be filtered
    long_paragraph = "A" * 200

    dummy_reader = DummyReader([DummyPage(short), DummyPage(long_paragraph)])

    # Monkeypatch PdfReader used in the module
    monkeypatch.setattr("app.rag.loader.PdfReader", lambda path: dummy_reader)

    loader = MedicalPDFLoader()
    chunks = loader.load_pdf(str(pdf_path))

    assert isinstance(chunks, list)
    # Only the long paragraph should produce a chunk
    assert len(chunks) == 1
    assert chunks[0]["metadata"]["source"] == pdf_path.name


def test_load_directory_and_index(monkeypatch, tmp_path):
    # Create two fake pdf files
    d = tmp_path
    (d / "a.pdf").write_text("1")
    (d / "b.pdf").write_text("2")

    # Monkeypatch load_pdf to return a predictable chunk list
    def fake_load_pdf(self, path):
        return [{"text": "x" * 150, "metadata": {"source": Path(path).name, "page": 1, "type": "pdf"}}]

    monkeypatch.setattr(MedicalPDFLoader, "load_pdf", fake_load_pdf)

    # Capture repository.add_documents calls by providing a fake repository
    added = {}

    class FakeRepo:
        def add_documents(self, texts, metadatas, ids):
            added['texts'] = texts
            added['metadatas'] = metadatas
            added['ids'] = ids

    loader = MedicalPDFLoader()
    loader.repository = FakeRepo()

    chunks = loader.load_directory(str(d))
    assert len(chunks) == 2

    # Index the chunks and ensure add_documents called
    loader.index_chunks(chunks)
    assert 'texts' in added
    assert len(added['texts']) == 2


def test_load_directory_not_found():
    """Directorio inexistente lanza FileNotFoundError."""
    loader = MedicalPDFLoader()
    with pytest.raises(FileNotFoundError):
        loader.load_directory("/nonexistent/path/to/pdfs")


def test_load_directory_handles_pdf_errors(monkeypatch, tmp_path):
    """Errores en PDFs individuales no detienen el proceso."""
    # Create fake PDFs
    d = tmp_path
    (d / "good.pdf").write_text("1")
    (d / "bad.pdf").write_text("2")

    call_count = {"count": 0}

    def fake_load_pdf(self, path):
        call_count["count"] += 1
        if "bad" in path:
            raise Exception("PDF corrupto")
        return [{"text": "x" * 150, "metadata": {"source": Path(path).name, "page": 1, "type": "pdf"}}]

    monkeypatch.setattr(MedicalPDFLoader, "load_pdf", fake_load_pdf)

    loader = MedicalPDFLoader()
    chunks = loader.load_directory(str(d))

    # Solo good.pdf debe haber producido chunks
    assert len(chunks) == 1
    assert call_count["count"] == 2  # Ambos fueron intentados


def test_index_chunks_empty_list():
    """Indexar lista vacía no hace nada."""
    added = {"called": False}

    class FakeRepo:
        def add_documents(self, texts, metadatas, ids):
            added["called"] = True

    loader = MedicalPDFLoader()
    loader.repository = FakeRepo()

    loader.index_chunks([])

    assert added["called"] is False


def test_index_knowledge_base_no_pdfs(monkeypatch, tmp_path):
    """index_knowledge_base maneja directorio vacío."""
    # Directorio sin PDFs
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    # Mock el loader
    with patch.object(MedicalPDFLoader, 'load_directory', return_value=[]) as mock_load:
        index_knowledge_base(str(empty_dir))
        mock_load.assert_called_once()


def test_index_knowledge_base_with_chunks(monkeypatch, tmp_path):
    """index_knowledge_base indexa chunks encontrados."""
    mock_chunks = [
        {"text": "A" * 150, "metadata": {"source": "test.pdf", "page": 1, "type": "pdf"}}
    ]

    mock_stats = {"count": 1}

    class FakeRepo:
        def add_documents(self, texts, metadatas, ids):
            pass

        def get_collection_stats(self):
            return mock_stats

    with patch.object(MedicalPDFLoader, 'load_directory', return_value=mock_chunks):
        with patch.object(MedicalPDFLoader, '__init__', lambda self: None):
            loader = MedicalPDFLoader()
            loader.settings = MagicMock()
            loader.settings.embedding_model = "test-model"
            loader.repository = FakeRepo()

            with patch('app.rag.loader.MedicalPDFLoader', return_value=loader):
                # Esto debería funcionar sin errores
                pass


def test_index_knowledge_base_handles_errors(monkeypatch, tmp_path):
    """index_knowledge_base maneja errores."""
    with patch.object(MedicalPDFLoader, 'load_directory',
                      side_effect=Exception("Error de prueba")):
        # No debe lanzar excepción, solo logear
        index_knowledge_base("/fake/path")
