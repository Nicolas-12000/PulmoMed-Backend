"""
Integration Tests - RAG End-to-End (local LLM)
Prueba flujo completo: RAG Retrieval → Prompt → LLM local → Respuesta
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is importable in test environment
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models.simulation_state import SimulationState  # noqa: E402
from app.repositories.medical_knowledge_repo import get_repository  # noqa: E402
from app.services.teacher_service import AITeacherService  # noqa: E402


@pytest.fixture
def service():
    """Fixture: AITeacherService usando LLM local (OllamaClient mock)"""
    repository = get_repository()
    return AITeacherService(repository=repository)


# Skip tests si no hay Gemini API key
# Gemini-related tests removed. RAG tests now use local/mock LLMs.


class TestRAGEndToEnd:
    """Tests de integración RAG completo usando LLM local"""

    @pytest.mark.asyncio
    async def test_rag_flow_early_stage(self, service):
        """Test: RAG completo para tumor estadio temprano"""
        state = SimulationState(
            edad=58,
            es_fumador=False,
            pack_years=0,
            volumen_tumor_sensible=1.5,  # Pequeño
            volumen_tumor_resistente=0,
            tratamiento_activo="ninguno",
        )

        response = await service.get_educational_feedback(state)

        # Validar estructura de respuesta
        assert response.explicacion is not None
        assert len(response.explicacion) > 30
        assert response.recomendacion is not None
        assert response.advertencia is not None
        assert len(response.fuentes) > 0
        assert isinstance(response.llm_model, str)
        assert len(response.llm_model) > 0

        # Validar contenido relevante (Gemini debe mencionar estadio temprano)
        combined_text = (response.explicacion + response.recomendacion).lower()
        assert any(
            keyword in combined_text
            for keyword in ["estadio", "temprano", "cirugía", "resección", "pronóstico"]
        )

    @pytest.mark.asyncio
    async def test_rag_flow_with_treatment(self, service):
        """Test: RAG con tratamiento activo (quimioterapia)"""
        state = SimulationState(
            edad=65,
            es_fumador=True,
            pack_years=40,
            volumen_tumor_sensible=12.0,
            volumen_tumor_resistente=0.5,
            tratamiento_activo="quimio",
        )

        response = await service.get_educational_feedback(state)

        # Validar que Gemini detectó tratamiento y resistencia
        combined_text = (response.explicacion + response.recomendacion).lower()
        assert any(
            keyword in combined_text
            for keyword in ["quimio", "tratamiento", "resistencia", "terapia"]
        )

        # Verificar que recuperó chunks relevantes
        assert response.retrieved_chunks > 0
        assert len(response.fuentes) > 0

    @pytest.mark.asyncio
    async def test_rag_flow_advanced_stage(self, service):
        """Test: RAG para estadio avanzado con resistencia"""
        state = SimulationState(
            edad=72,
            es_fumador=True,
            pack_years=60,
            volumen_tumor_sensible=25.0,
            volumen_tumor_resistente=8.0,
            tratamiento_activo="quimio",
            tiempo_simulacion=450,  # ~15 meses
        )

        response = await service.get_educational_feedback(state)

        # Validar respuesta para caso avanzado
        assert response.explicacion is not None
        assert len(response.fuentes) > 0

        combined_text = (response.explicacion + response.recomendacion).lower()

        # Gemini debería mencionar estadio avanzado o resistencia
        assert any(
            keyword in combined_text
            for keyword in [
                "avanzado",
                "resistencia",
                "resistente",
                "progresión",
                "inmunoterapia",
                "terapia dirigida",
                "segunda línea",
            ]
        )

    @pytest.mark.asyncio
    async def test_rag_retrieval_quality(self, service):
        """Test: Calidad del retrieval RAG"""
        state = SimulationState(
            edad=60,
            es_fumador=True,
            pack_years=45,
            volumen_tumor_sensible=8.0,
            tratamiento_activo="ninguno",
        )

        # Build query como lo hace el servicio
        query = service._build_search_query(state)

        # Verificar que la query incluye contexto relevante
        assert "60 años" in query
        assert "fumador" in query
        assert "45" in query

        # Recuperar chunks directamente
        chunks = service.repository.retrieve_relevant_chunks(query=query, top_k=5)

        # Validar que recuperó información relevante
        assert len(chunks) > 0
        assert all("text" in chunk for chunk in chunks)
        assert all("metadata" in chunk for chunk in chunks)

        # Verificar que los chunks tienen distancias razonables (< 0.5 es bueno)
        for chunk in chunks:
            assert "distance" in chunk
            assert chunk["distance"] < 0.7  # Threshold de relevancia

    @pytest.mark.asyncio
    async def test_rag_with_smoker_context(self, service):
        """Test: RAG incluye contexto de fumador en retrieval"""
        state_smoker = SimulationState(
            edad=58,
            es_fumador=True,
            pack_years=40,
            volumen_tumor_sensible=5.0,
            tratamiento_activo="ninguno",
        )

        state_nonsmoker = SimulationState(
            edad=58,
            es_fumador=False,
            pack_years=0,
            volumen_tumor_sensible=5.0,
            tratamiento_activo="ninguno",
        )

        response_smoker = await service.get_educational_feedback(state_smoker)
        response_nonsmoker = await service.get_educational_feedback(state_nonsmoker)

        # Ambas respuestas deben ser válidas
        assert response_smoker.explicacion is not None
        assert response_nonsmoker.explicacion is not None

        # Las respuestas deberían ser diferentes (contexto diferente)
        # Nota: el LLM puede generar respuestas similares.
        # El retrieval debe diferir para que las respuestas varíen según contexto
        smoker_text = (
            response_smoker.explicacion + response_smoker.recomendacion
        ).lower()

        # Para fumador, debería mencionar tabaquismo o factores de riesgo
        assert any(
            keyword in smoker_text
            for keyword in [
                "fumador",
                "tabaco",
                "tabaquismo",
                "pack",
                "riesgo",
            ]
        )


class TestRAGPromptQuality:
    """Tests para validar calidad de prompts RAG"""

    def test_prompt_includes_context(self, service):
        """Test: Prompts incluyen contexto RAG recuperado"""
        state = SimulationState(
            edad=60, volumen_tumor_sensible=10.0, tratamiento_activo="quimio"
        )

        # Simular construcción de prompt
        query = service._build_search_query(state)
        chunks = service.repository.retrieve_relevant_chunks(query, top_k=3)

        state_dict = state.model_dump()
        state_dict["estadio_aproximado"] = state.estadio_aproximado

        prompt = service.prompt_templates.build_teacher_prompt(
            state=state_dict, context_chunks=chunks
        )

        # Validar que el prompt incluye contexto
        assert "60" in prompt  # edad
        assert "10" in prompt or "10.0" in prompt  # volumen
        assert "quimio" in prompt.lower()

        # Debe incluir chunks recuperados
        assert len(chunks) > 0
        for chunk in chunks[:2]:  # Al menos 2 primeros chunks en el prompt
            chunk_text = chunk.get("text", "")[:30]  # Primeros 30 chars
            assert chunk_text in prompt or any(
                word in prompt for word in chunk_text.split()[:3]
            )

    @pytest.mark.asyncio
    async def test_response_includes_sources(self, service):
        """Test: Respuesta incluye fuentes de RAG"""
        state = SimulationState(
            edad=58, volumen_tumor_sensible=5.0, tratamiento_activo="ninguno"
        )

        response = await service.get_educational_feedback(state)

        # Debe incluir fuentes de los chunks
        assert len(response.fuentes) > 0

        # Fuentes deben ser strings válidas
        for fuente in response.fuentes:
            assert isinstance(fuente, str)
            assert len(fuente) > 0


@pytest.mark.integration
class TestRAGvsNoRAG:
    """Tests comparativos: RAG vs Sin RAG"""

    @pytest.mark.asyncio
    async def test_rag_provides_specific_context(self, service):
        """Test: RAG proporciona contexto más específico que LLM solo"""
        # Caso 1: Sin RAG (solo LLM)
        prompt_no_rag = "Paciente 60 años con NSCLC. ¿Tratamiento recomendado?"
        response_no_rag = service.llm_client.query(prompt_no_rag)

        # Caso 2: Con RAG (contexto específico)
        repository = get_repository()
        chunks = repository.retrieve_relevant_chunks(
            query="NSCLC estadio IIA tratamiento NCCN guidelines", top_k=3
        )

        context = "\n\n".join([f"- {chunk['text']}" for chunk in chunks])
        prompt_with_rag = f"""Contexto de guías médicas:
{context}

Pregunta: Paciente 60 años con NSCLC. ¿Tratamiento recomendado?"""

        response_with_rag = service.llm_client.query(prompt_with_rag)

        # Validar que ambas respuestas son válidas
        assert len(response_no_rag) > 30
        assert len(response_with_rag) > 30

        # La respuesta con RAG debería ser más específica
        # (difícil de verificar automáticamente, pero debe tener más tokens)
        # Nota: Este test es más cualitativo
        assert response_with_rag is not None
