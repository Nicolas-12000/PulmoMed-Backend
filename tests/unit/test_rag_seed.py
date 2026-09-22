from app.rag.seed import library_case_chunks, seed_library_cases
from app.rag.embeddings import HashEncoder
from app.repositories.medical_knowledge_repo import MedicalKnowledgeRepository


def test_library_case_chunks_are_indexable():
    chunks = library_case_chunks()
    assert len(chunks) >= 7
    assert all("text" in chunk and "metadata" in chunk for chunk in chunks)
    assert any(chunk["metadata"]["type"] == "seer_nccn" for chunk in chunks)


def test_seed_skips_missing_library(tmp_path):
    from app.rag.embeddings import HashEncoder
    from app.repositories.medical_knowledge_repo import MedicalKnowledgeRepository

    missing = tmp_path / "nope.json"
    assert library_case_chunks(missing) == []
    repo = MedicalKnowledgeRepository(encoder=HashEncoder())
    assert seed_library_cases(repo, missing) == 0


def test_seed_library_cases_populates_repository(tmp_path):
    repo = MedicalKnowledgeRepository(encoder=HashEncoder())
    count = seed_library_cases(repo)
    stats = repo.get_collection_stats()
    assert count == stats["count"]
    assert stats["count"] > 0

    hits = repo.retrieve_relevant_chunks("EGFR osimertinib adenocarcinoma no fumadora", top_k=3)
    assert hits
    assert hits[0]["distance"] < 1.0
