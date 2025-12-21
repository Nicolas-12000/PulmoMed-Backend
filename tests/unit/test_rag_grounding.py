import pytest

from app.llm.mock_llm import MockLLM
from app.models.simulation_state import SimulationState
from app.services.teacher_service import AITeacherService


class DummyRepo:
    def __init__(self, chunks):
        self._chunks = chunks

    def retrieve_relevant_chunks(self, query, top_k=None):
        return self._chunks


@pytest.mark.asyncio
async def test_response_includes_sources_and_uses_mockllm():
    chunks = [
        {"text": "Doc A content", "metadata": {"source": "docA"}, "distance": 0.2},
        {"text": "Doc B content", "metadata": {"source": "docB"}, "distance": 0.3},
    ]

    repo = DummyRepo(chunks)
    mock_llm = MockLLM(deterministic_responses={"tratamiento": "RESP_TRATAMIENTO"})
    service = AITeacherService(repository=repo, llm_client=mock_llm)

    state = SimulationState(
        age=60,
        is_smoker=False,
        pack_years=0,
        diet="normal",
        sensitive_tumor_volume=5.0,
        resistant_tumor_volume=0.0,
    )

    resp = await service.get_educational_feedback(state)
    assert isinstance(resp.sources, list)
    assert len(resp.sources) >= 1
    ok = (
        resp.llm_model in ("ollama-mock", "ollama-real", "mock")
        or "RESPUESTA_MOCK" in resp.explanation
        or "RESP_TRATAMIENTO" in resp.explanation
    )
    assert ok


@pytest.mark.asyncio
async def test_insufficient_info_returns_safe_message():
    repo = DummyRepo([])
    mock_llm = MockLLM()
    service = AITeacherService(repository=repo, llm_client=mock_llm)

    state = SimulationState(
        age=50,
        is_smoker=False,
        pack_years=0,
        diet="normal",
        sensitive_tumor_volume=0.1,
        resistant_tumor_volume=0.0,
    )

    resp = await service.get_educational_feedback(state)
    assert "No dispongo de información suficiente" in resp.explanation


@pytest.mark.asyncio
async def test_malicious_prompt_rejected(monkeypatch):
    # Create repo that returns normal chunks
    chunks = [{"text": "Doc", "metadata": {"source": "doc"}, "distance": 0.2}]
    repo = DummyRepo(chunks)
    mock_llm = MockLLM()
    service = AITeacherService(repository=repo, llm_client=mock_llm)

    # Monkeypatch the search query builder to return a malicious string
    monkeypatch.setattr(service, "_build_search_query", lambda state: "rm -rf /")

    state = SimulationState(
        age=45,
        is_smoker=False,
        pack_years=0,
        diet="normal",
        sensitive_tumor_volume=3.0,
        resistant_tumor_volume=0.0,
    )

    resp = await service.get_educational_feedback(state)
    assert "Solicitud rechazada" in resp.explanation or "rechazada" in (resp.warning or "")
