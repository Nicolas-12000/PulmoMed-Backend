"""
Unit Tests - Domain Models
Prueba validaciones Pydantic y lógica de negocio
"""
import pytest
from pydantic import ValidationError
from app.models.simulation_state import SimulationState, TeacherResponse, CasoBiblioteca


class TestSimulationState:
    """Tests para modelo SimulationState"""
    
    def test_valid_state_creation(self):
        """Test: Creación válida de estado"""
        state = SimulationState(
            edad=55,
            es_fumador=True,
            pack_years=30.0,
            dieta="normal",
            volumen_tumor_sensible=10.5,
            volumen_tumor_resistente=1.2,
            tratamiento_activo="quimio"
        )
        
        assert state.edad == 55
        assert state.volumen_total == 11.7
        assert state.tratamiento_activo == "quimio"
    
    def test_age_validation_fails(self):
        """Test: Validación edad fuera de rango"""
        with pytest.raises(ValidationError) as exc_info:
            SimulationState(
                edad=150,  # Invalid
                volumen_tumor_sensible=5.0
            )
        
        assert "edad" in str(exc_info.value)
    
    def test_pack_years_validation_non_smoker(self):
        """Test: pack_years > 0 sin ser fumador debe fallar"""
        with pytest.raises(ValidationError):
            SimulationState(
                edad=60,
                es_fumador=False,
                pack_years=20.0,  # Invalid para no fumador
                volumen_tumor_sensible=5.0
            )
    
    def test_estadio_aproximado_calculation(self):
        """Test: Cálculo correcto de estadio TNM aproximado"""
        test_cases = [
            (2.0, "IA (T1a)"),
            (10.0, "IB (T2a)"),
            (20.0, "IIA (T2b)"),
            (40.0, "IIB (T3)"),
            (80.0, "IIIA+ (T4 o avanzado)")
        ]
        
        for volumen, estadio_esperado in test_cases:
            state = SimulationState(
                edad=60,
                volumen_tumor_sensible=volumen
            )
            assert state.estadio_aproximado == estadio_esperado
    
    def test_volumen_total_property(self):
        """Test: Propiedad calculada volumen_total"""
        state = SimulationState(
            edad=55,
            volumen_tumor_sensible=8.5,
            volumen_tumor_resistente=1.5
        )
        
        assert state.volumen_total == 10.0


class TestTeacherResponse:
    """Tests para modelo TeacherResponse"""
    
    def test_valid_response_creation(self):
        """Test: Creación válida de respuesta"""
        response = TeacherResponse(
            explicacion="El tumor crece según Gompertz",
            recomendacion="Consultar oncólogo",
            fuentes=["NCCN Guidelines 2024"],
            retrieved_chunks=5
        )
        
        assert response.explicacion != ""
        assert response.llm_model == "mock"
        assert len(response.fuentes) == 1
    
    def test_response_with_warning(self):
        """Test: Respuesta con advertencia educativa"""
        response = TeacherResponse(
            explicacion="Análisis",
            recomendacion="Acción",
            advertencia="Este es un simulador educativo"
        )
        
        assert response.advertencia is not None
        assert "educativo" in response.advertencia.lower()


class TestCasoBiblioteca:
    """Tests para modelo CasoBiblioteca"""
    
    def test_valid_caso_creation(self):
        """Test: Creación válida de caso predefinido"""
        caso = CasoBiblioteca(
            caso_id="TEST_001",
            titulo="Caso de Prueba",
            descripcion="Paciente ficticio para testing",
            edad=60,
            es_fumador=True,
            pack_years=35.0,
            dieta="normal",
            volumen_inicial_sensible=15.0,
            fuente_estadistica="SEER 2020"
        )
        
        assert caso.caso_id == "TEST_001"
        assert caso.edad == 60
        assert caso.volumen_inicial_resistente == 0.0  # Default
    
    def test_caso_with_learning_objectives(self):
        """Test: Caso con objetivos de aprendizaje"""
        caso = CasoBiblioteca(
            caso_id="TEST_002",
            titulo="Test",
            descripcion="Test",
            edad=50,
            es_fumador=False,
            pack_years=0,
            dieta="saludable",
            volumen_inicial_sensible=5.0,
            fuente_estadistica="Test",
            objetivos_aprendizaje=[
                "Objetivo 1",
                "Objetivo 2"
            ]
        )
        
        assert len(caso.objetivos_aprendizaje) == 2
