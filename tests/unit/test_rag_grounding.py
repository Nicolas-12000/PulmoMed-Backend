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
        edad=60,
        es_fumador=False,
        pack_years=0,
        dieta="normal",
        volumen_tumor_sensible=5.0,
        volumen_tumor_resistente=0.0,
    )

    resp = await service.get_educational_feedback(state)
    assert isinstance(resp.fuentes, list)
    assert len(resp.fuentes) >= 1
    assert resp.llm_model in ("ollama-mock", "ollama-real", "mock") or "RESPUESTA_MOCK" in resp.explicacion or "RESP_TRATAMIENTO" in resp.explicacion


@pytest.mark.asyncio
async def test_insufficient_info_returns_safe_message():
    repo = DummyRepo([])
    mock_llm = MockLLM()
    service = AITeacherService(repository=repo, llm_client=mock_llm)

    state = SimulationState(
        edad=50,
        es_fumador=False,
        pack_years=0,
        dieta="normal",
        volumen_tumor_sensible=0.1,
        volumen_tumor_resistente=0.0,
    )

    resp = await service.get_educational_feedback(state)
    assert "No dispongo de información suficiente" in resp.explicacion


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
        edad=45,
        es_fumador=False,
        pack_years=0,
        dieta="normal",
        volumen_tumor_sensible=3.0,
        volumen_tumor_resistente=0.0,
    )

    resp = await service.get_educational_feedback(state)
    assert "Solicitud rechazada" in resp.explicacion or "rechazada" in (resp.advertencia or "")
