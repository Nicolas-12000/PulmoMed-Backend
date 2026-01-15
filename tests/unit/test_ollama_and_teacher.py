import pytest

from app.llm.ollama_client import OllamaClient
from app.services.teacher_service import AITeacherService
from app.models.simulation_state import SimulationState


@pytest.mark.asyncio
async def test_ollama_mock_responses():
    c = OllamaClient()
    # Default mock not available
    assert c.check_availability() is False

    resp_trat = await c.query("¿Cuál es el mejor tratamiento?")
    assert "Recomendación Educativa" in resp_trat or "Estadio" in resp_trat

    resp_prog = await c.query("Evolución de la progresión y volumen")
    assert "Análisis de Progresión" in resp_prog or "Progresión" in resp_prog


class DummyRepo:
    def __init__(self, chunks):
        self._chunks = chunks

    def retrieve_relevant_chunks(self, query, top_k=5):
        return self._chunks


class SimpleLLM:
    """Simple async LLM mock for tests"""
    def __init__(self, response: str):
        self._response = response

    async def query(self, prompt: str) -> str:
        return self._response

    def check_availability(self) -> bool:
        return False


@pytest.mark.asyncio
async def test_teacher_service_insufficient_and_malicious(monkeypatch):
    # Repository returns no chunks -> insufficient info
    repo = DummyRepo([])
    svc = AITeacherService(repository=repo, llm_client=SimpleLLM("ok"))

    state = SimulationState(
        age=30,
        is_smoker=False,
        pack_years=0.0,
        days_since_smoking_change=0,
        lung_state=None,
        diet="normal",
        sensitive_tumor_volume=0.0,
        resistant_tumor_volume=0.0,
        active_treatment="ninguno",
        treatment_days=0,
    )

    resp = await svc.get_educational_feedback(state)
    assert "No dispongo de información suficiente" in resp.explanation

    # Now test malicious prompt detection: monkeypatch prompt builder to return malicious content
    class PT:
        def build_teacher_prompt(self, state, context_chunks):
            return "rm -rf /"

    svc.prompt_templates = PT()
    # Fake repository returns a chunk under threshold
    svc.repository = DummyRepo([{"metadata": {"source": "kb.pdf"}, "distance": 0.1, "text": "x"}])
    resp2 = await svc.get_educational_feedback(state)
    assert "Solicitud rechazada" in resp2.explanation or resp2.llm_model == "safety-filter"


@pytest.mark.asyncio
async def test_teacher_service_parse_full_flow(monkeypatch):
    # Prepare a response with explicit sections
    llm_text = (
        "**Explicación:**\nDetalle explicativo\n"
        "**Recomendación Educativa:**\nHacer A\n"
        "**Disclaimer:**\nN/A"
    )
    svc = AITeacherService(
        repository=DummyRepo([
            {"metadata": {"source": "x"}, "distance": 0.01, "text": "t"}
        ]),
        llm_client=SimpleLLM(llm_text),
    )

    state = SimulationState(
        age=60,
        is_smoker=True,
        pack_years=10.0,
        days_since_smoking_change=0,
        lung_state=None,
        diet="normal",
        sensitive_tumor_volume=5.0,
        resistant_tumor_volume=0.0,
        active_treatment="ninguno",
        treatment_days=0,
    )

    resp = await svc.get_educational_feedback(state)
    assert "Detalle explicativo" in resp.explanation
    assert resp.sources and "x" in resp.sources[0]
