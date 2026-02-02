"""
Tests for simulation.py - SimulationRunner and related functions.
Tests de integración del runner de simulaciones.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from math_model.simulation import (
    SimulationRunner,
    SimulationResult,
    create_sample_patient,
    quick_simulation_test,
)
from math_model.patient_profile import DietType
from math_model.treatments import get_treatment


# =============================================================================
# SimulationResult Tests
# =============================================================================

class TestSimulationResult:
    """Tests para SimulationResult dataclass."""

    def test_simulation_result_creation(self):
        """SimulationResult se puede crear correctamente."""
        patient = create_sample_patient("typical")
        result = SimulationResult(
            patient=patient,
            initial_volume=5.0,
            final_volume=8.0,
            final_sensitive=6.0,
            final_resistant=2.0,
            days_simulated=90,
            treatment_name="Quimioterapia",
            final_stage="II",
            daily_states=[],
            backend_responses=[],
        )
        assert result.initial_volume == 5.0
        assert result.final_volume == 8.0
        assert result.days_simulated == 90

    def test_simulation_result_to_dict(self):
        """to_dict serializa correctamente."""
        patient = create_sample_patient("typical")
        result = SimulationResult(
            patient=patient,
            initial_volume=5.0,
            final_volume=8.0,
            final_sensitive=6.0,
            final_resistant=2.0,
            days_simulated=90,
            treatment_name="None",
            final_stage="II",
        )
        data = result.to_dict()
        assert "patient" in data
        assert data["initial_volume"] == 5.0
        assert data["final_volume"] == 8.0
        assert data["days_simulated"] == 90
        assert "timestamp" in data

    def test_simulation_result_default_values(self):
        """Valores por defecto se establecen."""
        patient = create_sample_patient("typical")
        result = SimulationResult(
            patient=patient,
            initial_volume=5.0,
            final_volume=8.0,
            final_sensitive=6.0,
            final_resistant=2.0,
            days_simulated=90,
            treatment_name="None",
            final_stage="II",
        )
        assert result.daily_states == []
        assert result.backend_responses == []
        assert result.simulation_time_ms == 0.0
        assert result.timestamp is not None


# =============================================================================
# SimulationRunner Tests
# =============================================================================

class TestSimulationRunner:
    """Tests para SimulationRunner."""

    def test_runner_initialization(self):
        """Runner se inicializa correctamente."""
        runner = SimulationRunner(backend_url="http://test:8000")
        assert runner.backend_url == "http://test:8000"
        assert runner.timeout == 30.0

    def test_runner_strips_trailing_slash(self):
        """Runner elimina slash final de la URL."""
        runner = SimulationRunner(backend_url="http://test:8000/")
        assert runner.backend_url == "http://test:8000"

    def test_runner_custom_timeout(self):
        """Runner acepta timeout personalizado."""
        runner = SimulationRunner(timeout=60.0)
        assert runner.timeout == 60.0

    @pytest.mark.asyncio
    async def test_get_client_lazy_init(self):
        """Cliente se inicializa lazy."""
        runner = SimulationRunner()
        assert runner._client is None
        client = await runner._get_client()
        assert client is not None
        assert runner._client is client
        await runner.close()

    @pytest.mark.asyncio
    async def test_close_releases_client(self):
        """close() libera el cliente."""
        runner = SimulationRunner()
        await runner._get_client()  # Initialize
        await runner.close()
        assert runner._client is None

    @pytest.mark.asyncio
    async def test_close_when_no_client(self):
        """close() funciona sin cliente inicializado."""
        runner = SimulationRunner()
        await runner.close()  # Should not raise
        assert runner._client is None


# =============================================================================
# Backend Communication Tests
# =============================================================================

class TestBackendCommunication:
    """Tests para comunicación con backend."""

    @pytest.mark.asyncio
    async def test_check_backend_health_success(self):
        """Health check exitoso."""
        runner = SimulationRunner()

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(runner, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await runner.check_backend_health()

        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_check_backend_health_error(self):
        """Health check con error."""
        runner = SimulationRunner()

        with patch.object(runner, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Connection failed"))
            mock_get_client.return_value = mock_client

            result = await runner.check_backend_health()

        assert result["status"] == "error"
        assert "Connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_consult_professor_success(self):
        """Consulta al profesor exitosa."""
        runner = SimulationRunner()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "El tumor está creciendo",
            "recommendations": ["Iniciar tratamiento"]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(runner, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            state = {
                "age": 60,
                "is_smoker": False,
                "sensitive_tumor_volume": 5.0,
            }
            result = await runner.consult_professor(state)

        assert "response" in result
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_consult_professor_http_error(self):
        """Consulta al profesor con error HTTP."""
        runner = SimulationRunner()

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        http_error = httpx.HTTPStatusError(
            "Error",
            request=MagicMock(),
            response=mock_response
        )

        with patch.object(runner, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=http_error)
            mock_get_client.return_value = mock_client

            result = await runner.consult_professor({})

        assert result.get("error") is True
        assert result.get("status_code") == 401

    @pytest.mark.asyncio
    async def test_consult_professor_generic_error(self):
        """Consulta al profesor con error genérico."""
        runner = SimulationRunner()

        with patch.object(runner, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=Exception("Network error"))
            mock_get_client.return_value = mock_client

            result = await runner.consult_professor({})

        assert result.get("error") is True
        assert "Network error" in result.get("detail", "")


# =============================================================================
# Run Simulation Tests
# =============================================================================

class TestRunSimulation:
    """Tests para run_simulation."""

    @pytest.mark.asyncio
    async def test_run_simulation_no_treatment(self):
        """Simulación sin tratamiento."""
        runner = SimulationRunner()
        patient = create_sample_patient("typical")

        # Mock consult_professor para no hacer llamadas reales
        with patch.object(runner, 'consult_professor', new_callable=AsyncMock) as mock_consult:
            mock_consult.return_value = {"status": "ok"}

            result = await runner.run_simulation(
                patient=patient,
                initial_volume=5.0,
                days=30,
                treatment=None,
                consult_interval=0,  # No consultar
            )

        assert result.initial_volume == 5.0
        assert result.days_simulated == 30
        assert result.treatment_name == "Ninguno"
        assert len(result.daily_states) == 30

    @pytest.mark.asyncio
    async def test_run_simulation_with_treatment(self):
        """Simulación con tratamiento."""
        runner = SimulationRunner()
        patient = create_sample_patient("typical")
        treatment = get_treatment("chemotherapy")

        with patch.object(runner, 'consult_professor', new_callable=AsyncMock):
            result = await runner.run_simulation(
                patient=patient,
                initial_volume=5.0,
                days=30,
                treatment=treatment,
                treatment_start_day=7,
                consult_interval=0,
            )

        assert result.treatment_name == treatment.name
        assert result.days_simulated == 30

    @pytest.mark.asyncio
    async def test_run_simulation_with_consult(self):
        """Simulación con consultas al profesor."""
        runner = SimulationRunner()
        patient = create_sample_patient("typical")

        with patch.object(runner, 'consult_professor', new_callable=AsyncMock) as mock_consult:
            mock_consult.return_value = {"response": "Consulta exitosa"}

            result = await runner.run_simulation(
                patient=patient,
                initial_volume=5.0,
                days=60,
                consult_interval=30,  # Consultar cada 30 días
            )

        assert len(result.backend_responses) == 2  # Día 30 y 60
        assert mock_consult.call_count == 2

    @pytest.mark.asyncio
    async def test_run_simulation_resistant_fraction(self):
        """Simulación con fracción resistente inicial."""
        runner = SimulationRunner()
        patient = create_sample_patient("typical")

        with patch.object(runner, 'consult_professor', new_callable=AsyncMock):
            result = await runner.run_simulation(
                patient=patient,
                initial_volume=10.0,
                days=10,
                initial_resistant_fraction=0.2,
                consult_interval=0,
            )

        # La fracción inicial debería reflejarse
        assert result.initial_volume == 10.0
        # El resultado final debería tener componentes resistentes
        assert result.final_resistant >= 0

    @pytest.mark.asyncio
    async def test_run_simulation_records_time(self):
        """Simulación registra tiempo de ejecución."""
        runner = SimulationRunner()
        patient = create_sample_patient("typical")

        with patch.object(runner, 'consult_professor', new_callable=AsyncMock):
            result = await runner.run_simulation(
                patient=patient,
                initial_volume=5.0,
                days=10,
                consult_interval=0,
            )

        assert result.simulation_time_ms > 0

    def test_run_simulation_sync(self):
        """Versión síncrona de simulación."""
        runner = SimulationRunner()
        patient = create_sample_patient("typical")

        with patch.object(runner, 'consult_professor', new_callable=AsyncMock):
            result = runner.run_simulation_sync(
                patient=patient,
                initial_volume=5.0,
                days=10,
                consult_interval=0,
            )

        assert result.days_simulated == 10


# =============================================================================
# Create Sample Patient Tests
# =============================================================================

class TestCreateSamplePatient:
    """Tests para create_sample_patient."""

    def test_typical_patient(self):
        """Paciente típico."""
        patient = create_sample_patient("typical")
        assert patient.age == 62
        assert not patient.is_smoker
        assert patient.diet == DietType.NORMAL

    def test_young_healthy_patient(self):
        """Paciente joven y saludable."""
        patient = create_sample_patient("young_healthy")
        assert patient.age == 35
        assert not patient.is_smoker
        assert patient.diet == DietType.HEALTHY

    def test_elderly_smoker_patient(self):
        """Paciente adulto mayor fumador."""
        patient = create_sample_patient("elderly_smoker")
        assert patient.age == 72
        assert patient.is_smoker
        assert patient.pack_years == 45
        assert patient.diet == DietType.POOR

    def test_high_risk_patient(self):
        """Paciente de alto riesgo."""
        patient = create_sample_patient("high_risk")
        assert patient.age == 68
        assert patient.is_smoker
        assert patient.pack_years == 60
        assert patient.genetic_factor == 1.3

    def test_unknown_scenario_defaults_to_typical(self):
        """Escenario desconocido retorna típico."""
        patient = create_sample_patient("unknown_scenario")
        typical = create_sample_patient("typical")
        assert patient.age == typical.age
        assert patient.is_smoker == typical.is_smoker


# =============================================================================
# Quick Simulation Test Function
# =============================================================================

class TestQuickSimulationTest:
    """Tests para quick_simulation_test."""

    @pytest.mark.asyncio
    async def test_quick_simulation_backend_unavailable(self):
        """Simulación rápida con backend no disponible."""
        with patch.object(SimulationRunner, 'check_backend_health', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = {"status": "error", "error": "No connection"}
            with patch.object(SimulationRunner, 'close', new_callable=AsyncMock):
                result = await quick_simulation_test()

        assert "error" in result
        assert "Backend no disponible" in result.get("error", "")

    @pytest.mark.asyncio
    async def test_quick_simulation_success(self):
        """Simulación rápida exitosa."""
        mock_result = SimulationResult(
            patient=create_sample_patient("elderly_smoker"),
            initial_volume=5.0,
            final_volume=3.0,
            final_sensitive=2.0,
            final_resistant=1.0,
            days_simulated=90,
            treatment_name="Chemotherapy",
            final_stage="II",
            backend_responses=[{"day": 30}, {"day": 60}, {"day": 90}],
            simulation_time_ms=100.0,
        )

        with patch.object(SimulationRunner, 'check_backend_health', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = {"status": "ok"}
            with patch.object(SimulationRunner, 'run_simulation', new_callable=AsyncMock) as mock_run:
                mock_run.return_value = mock_result
                with patch.object(SimulationRunner, 'close', new_callable=AsyncMock):
                    result = await quick_simulation_test()

        assert result.get("success") is True
        assert result["initial_volume"] == 5.0
        assert result["final_volume"] == 3.0
        assert result["backend_consultations"] == 3


# =============================================================================
# Daily State Recording Tests
# =============================================================================

class TestDailyStateRecording:
    """Tests para registro de estados diarios."""

    @pytest.mark.asyncio
    async def test_daily_states_recorded(self):
        """Estados diarios se registran correctamente."""
        runner = SimulationRunner()
        patient = create_sample_patient("typical")

        with patch.object(runner, 'consult_professor', new_callable=AsyncMock):
            result = await runner.run_simulation(
                patient=patient,
                initial_volume=5.0,
                days=5,
                consult_interval=0,
            )

        assert len(result.daily_states) == 5
        for i, state in enumerate(result.daily_states):
            assert state["day"] == i + 1
            assert "sensitive" in state
            assert "resistant" in state
            assert "total" in state
            assert "stage" in state

    @pytest.mark.asyncio
    async def test_daily_states_show_progression(self):
        """Estados diarios muestran progresión (sin tratamiento)."""
        runner = SimulationRunner()
        patient = create_sample_patient("typical")

        with patch.object(runner, 'consult_professor', new_callable=AsyncMock):
            result = await runner.run_simulation(
                patient=patient,
                initial_volume=5.0,
                days=30,
                treatment=None,
                consult_interval=0,
            )

        # Sin tratamiento, el tumor debería crecer
        first_day = result.daily_states[0]
        last_day = result.daily_states[-1]
        assert last_day["total"] > first_day["total"]
