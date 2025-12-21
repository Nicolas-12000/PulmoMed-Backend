import os
from pathlib import Path

import pytest

from app.rag.loader import MedicalPDFLoader


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
