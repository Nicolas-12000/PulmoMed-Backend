"""
Unit Tests - Service Layer
Prueba lógica de negocio del AI Teacher Service
"""

from unittest.mock import Mock

import pytest

from app.models.simulation_state import SimulationState, TeacherResponse
from app.services.teacher_service import AITeacherService


@pytest.fixture
def mock_repository():
    """Mock del repositorio"""
    repo = Mock()
    repo.retrieve_relevant_chunks = Mock(
        return_value=[
            {
                "text": "El estadio IA tiene supervivencia del 80-90% con cirugía.",
                "metadata": {"source": "NCCN_Guidelines.pdf", "page": 15},
                "distance": 0.25,
            },
            {
                "text": (
                    "La resección quirúrgica es el tratamiento de elección "
                    "en estadios tempranos."
                ),
                "metadata": {"source": "SEER_Data.pdf", "page": 42},
                "distance": 0.31,
            },
        ]
    )
    return repo


@pytest.fixture
def mock_llm_client():
    """Mock del cliente LLM"""
    llm = Mock()
    llm.query = Mock(
        return_value=(
            "**Explicación del Estado Actual:**\n"
            "El tumor está en estadio temprano con excelente pronóstico.\n\n"
            "**Recomendación Educativa:**\n"
            "Resección quirúrgica según guías NCCN.\n\n"
            "**Disclaimer:** Simulador educativo."
        )
    )
    llm.check_availability = Mock(return_value=False)
    return llm


@pytest.fixture
def service(mock_repository, mock_llm_client):
    """Fixture: Service con mocks inyectados"""
    return AITeacherService(repository=mock_repository, llm_client=mock_llm_client)


class TestAITeacherService:
    """Tests para AI Teacher Service"""

    @pytest.mark.asyncio
    async def test_get_educational_feedback_success(self, service, mock_repository):
        """Test: Generación exitosa de feedback educativo"""
        state = SimulationState(
            edad=58,
            es_fumador=False,
            pack_years=0,
            volumen_tumor_sensible=2.5,
            tratamiento_activo="ninguno",
        )

        response = await service.get_educational_feedback(state)

        assert isinstance(response, TeacherResponse)
        assert response.explicacion != ""
        assert response.recomendacion != ""
        assert len(response.fuentes) > 0
        assert response.advertencia is not None
        assert mock_repository.retrieve_relevant_chunks.called

    @pytest.mark.asyncio
    async def test_build_search_query_smoker(self, service):
        """Test: Construcción de query para fumador"""
        state = SimulationState(
            edad=67,
            es_fumador=True,
            pack_years=45.0,
            volumen_tumor_sensible=18.0,
            tratamiento_activo="quimio",
        )

        query = service._build_search_query(state)

        assert "67 años" in query
        assert "fumador" in query
        assert "45" in query
        assert "quimio" in query

    @pytest.mark.asyncio
    async def test_build_search_query_with_resistance(self, service):
        """Test: Query incluye resistencia si hay células resistentes"""
        state = SimulationState(
            edad=60,
            volumen_tumor_sensible=10.0,
            volumen_tumor_resistente=3.0,
            tratamiento_activo="quimio",
        )

        query = service._build_search_query(state)

        assert "resistencia" in query.lower()

    @pytest.mark.asyncio
    async def test_parse_llm_response(self, service):
        """Test: Parseo correcto de respuesta del LLM"""
        llm_response = """**Explicación del Estado Actual:**
Tumor en crecimiento exponencial.

**Recomendación Educativa:**
Considerar tratamiento según NCCN.

**Disclaimer:** Simulador educativo."""

        chunks = [
            {"text": "Contenido", "metadata": {"source": "test.pdf"}, "distance": 0.2}
        ]

        state = SimulationState(edad=60, volumen_tumor_sensible=5.0)

        response = service._parse_llm_response(llm_response, chunks, state)

        assert "Tumor en crecimiento" in response.explicacion
        assert "NCCN" in response.recomendacion
        assert len(response.fuentes) > 0
        assert response.advertencia is not None

    @pytest.mark.asyncio
    async def test_feedback_with_empty_chunks(self, service, mock_repository):
        """Test: Service maneja correctamente retrieval vacío"""
        mock_repository.retrieve_relevant_chunks = Mock(return_value=[])

        state = SimulationState(edad=55, volumen_tumor_sensible=8.0)

        response = await service.get_educational_feedback(state)

        # Debe retornar respuesta válida incluso sin chunks
        assert isinstance(response, TeacherResponse)
        assert response.retrieved_chunks == 0
