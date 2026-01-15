"""
Unit Tests - Domain Models
Prueba validaciones Pydantic y lógica de negocio
"""

import pytest
from pydantic import ValidationError

from app.models.simulation_state import LibraryCase, SimulationState, TeacherResponse


class TestSimulationState:
    """Tests para modelo SimulationState"""

    def test_valid_state_creation(self):
        """Test: Creación válida de estado"""
        state = SimulationState(
            age=55,
            is_smoker=True,
            pack_years=30.0,
            diet="normal",
            sensitive_tumor_volume=10.5,
            resistant_tumor_volume=1.2,
            active_treatment="quimio",
        )

        assert state.age == 55
        assert state.total_volume == 11.7
        assert state.active_treatment == "quimio"

    def test_age_validation_fails(self):
        """Test: Validación edad fuera de rango"""
        with pytest.raises(ValidationError) as exc_info:
            SimulationState(age=150, sensitive_tumor_volume=5.0)  # Invalid

        assert "age" in str(exc_info.value)

    def test_pack_years_validation_non_smoker(self):
        """Test: pack_years > 0 sin ser fumador debe fallar"""
        with pytest.raises(ValidationError):
            SimulationState(
                age=60,
                is_smoker=False,
                pack_years=20.0,  # Invalid para no fumador
                sensitive_tumor_volume=5.0,
            )

    def test_estadio_aproximado_calculation(self):
        """Test: Cálculo correcto de estadio TNM aproximado"""
        test_cases = [
            (2.0, "IA (T1a)"),
            (10.0, "IB (T2a)"),
            (20.0, "IIA (T2b)"),
            (40.0, "IIB (T3)"),
            (80.0, "IIIA+ (T4 o avanzado)"),
        ]

        for volumen, estadio_esperado in test_cases:
            state = SimulationState(age=60, sensitive_tumor_volume=volumen)
            assert state.approx_stage == estadio_esperado

    def test_volumen_total_property(self):
        """Test: Propiedad calculada volumen_total"""
        state = SimulationState(
            age=55, sensitive_tumor_volume=8.5, resistant_tumor_volume=1.5
        )

        assert state.total_volume == 10.0


class TestTeacherResponse:
    """Tests para modelo TeacherResponse"""

    def test_valid_response_creation(self):
        """Test: Creación válida de respuesta"""
        response = TeacherResponse(
            explanation="El tumor crece según Gompertz",
            recommendation="Consultar oncólogo",
            sources=["NCCN Guidelines 2024"],
            retrieved_chunks=5,
        )

        assert response.explanation != ""
        assert response.llm_model == "mock"
        assert len(response.sources) == 1

    def test_response_with_warning(self):
        """Test: Respuesta con advertencia educativa"""
        response = TeacherResponse(
            explanation="Análisis",
            recommendation="Acción",
            warning="Este es un simulador educativo",
        )

        assert response.warning is not None
        assert "educativo" in response.warning.lower()


class TestLibraryCase:
    """Tests para modelo LibraryCase"""

    def test_valid_case_creation(self):
        """Test: Creación válida de caso predefinido"""
        case = LibraryCase(
            caso_id="TEST_001",
            titulo="Caso de Prueba",
            descripcion="Paciente ficticio para testing",
            edad=60,
            es_fumador=True,
            pack_years=35.0,
            dieta="normal",
            volumen_inicial_sensible=15.0,
            fuente_estadistica="SEER 2020",
        )

        assert case.case_id == "TEST_001"
        assert case.age == 60
        assert case.initial_resistant_volume == 0.0  # Default

    def test_case_with_learning_objectives(self):
        """Test: Caso con objetivos de aprendizaje"""
        case = LibraryCase(
            caso_id="TEST_002",
            titulo="Test",
            descripcion="Test",
            edad=50,
            es_fumador=False,
            pack_years=0,
            dieta="saludable",
            volumen_inicial_sensible=5.0,
            fuente_estadistica="Test",
            objetivos_aprendizaje=["Objetivo 1", "Objetivo 2"],
        )

        assert len(case.learning_objectives) == 2
