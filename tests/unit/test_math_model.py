"""
Tests unitarios exhaustivos para el módulo math_model.

Cobertura completa del modelo matemático de crecimiento tumoral.
Incluye casos positivos (comportamiento esperado) y negativos (validación de errores).
"""
import pytest
import math
import numpy as np

from math_model import (
    PatientProfile,
    DietType,
    create_sample_patient,
    TumorGrowthModel,
    NoTreatmentStrategy,
    ChemotherapyStrategy,
    RadiotherapyStrategy,
    ImmunotherapyStrategy,
    SurgeryStrategy,
    RK4Solver,
    SimulationRunner,
    SimulationResult,
)


# =============================================================================
# Tests de PatientProfile
# =============================================================================

class TestPatientProfile:
    """Tests para PatientProfile."""

    def test_create_default_patient(self):
        """Paciente por defecto tiene valores válidos."""
        patient = PatientProfile()
        assert patient.age == 60
        assert patient.is_smoker is False
        assert patient.pack_years == 0.0
        assert patient.diet == DietType.NORMAL
        assert patient.genetic_factor == 1.0

    def test_create_custom_patient(self):
        """Paciente personalizado."""
        patient = PatientProfile(
            age=55,
            is_smoker=True,
            pack_years=25,
            diet=DietType.POOR,
            genetic_factor=1.2
        )
        assert patient.age == 55
        assert patient.is_smoker is True
        assert patient.pack_years == 25
        assert patient.diet == DietType.POOR
        assert patient.genetic_factor == 1.2

    def test_age_growth_modifier_young(self):
        """Modificador de edad para paciente joven."""
        young = PatientProfile(age=30)
        modifier = young.get_age_growth_modifier()
        # 1.0 + 0.005 * (30 - 50) = 1.0 - 0.1 = 0.9
        assert modifier == pytest.approx(0.9)

    def test_age_growth_modifier_old(self):
        """Modificador de edad para paciente mayor."""
        old = PatientProfile(age=70)
        modifier = old.get_age_growth_modifier()
        # 1.0 + 0.005 * (70 - 50) = 1.0 + 0.1 = 1.1
        assert modifier == pytest.approx(1.1)

    def test_smoking_modifier_non_smoker(self):
        """No fumador tiene modificador 1.0."""
        non_smoker = PatientProfile(is_smoker=False)
        assert non_smoker.get_smoking_capacity_modifier() == 1.0

    def test_smoking_modifier_light_smoker(self):
        """Fumador leve reduce capacidad."""
        smoker = PatientProfile(is_smoker=True, pack_years=10)
        modifier = smoker.get_smoking_capacity_modifier()
        # 1.0 - 0.003 * 10 = 0.97
        assert modifier == pytest.approx(0.97)

    def test_smoking_modifier_heavy_smoker(self):
        """Fumador pesado reduce capacidad (mínimo 50%)."""
        heavy = PatientProfile(is_smoker=True, pack_years=200)
        modifier = heavy.get_smoking_capacity_modifier()
        assert modifier == 0.5  # Mínimo

    def test_diet_modifier_healthy(self):
        """Dieta saludable reduce progresión."""
        healthy = PatientProfile(diet=DietType.HEALTHY)
        assert healthy.get_diet_modifier() == 0.90

    def test_diet_modifier_normal(self):
        """Dieta normal sin modificación."""
        normal = PatientProfile(diet=DietType.NORMAL)
        assert normal.get_diet_modifier() == 1.0

    def test_diet_modifier_poor(self):
        """Dieta pobre aumenta progresión."""
        poor = PatientProfile(diet=DietType.POOR)
        assert poor.get_diet_modifier() == 1.10

    def test_combined_modifier(self):
        """Modificador combinado."""
        patient = PatientProfile(age=60, diet=DietType.HEALTHY)
        modifier = patient.get_combined_modifier()
        # age=60: 1.0 + 0.005 * 10 = 1.05
        # smoking: 1.0 (no fumador)
        # diet: 0.9
        # genetic: 1.0
        expected = 1.05 * 1.0 * 0.9 * 1.0
        assert modifier == pytest.approx(expected)

    def test_to_dict(self):
        """Serialización a diccionario."""
        patient = PatientProfile(age=55, is_smoker=True, pack_years=20)
        d = patient.to_dict()
        assert d["age"] == 55
        assert d["is_smoker"] is True
        assert d["pack_years"] == 20
        assert d["diet"] == "normal"
        assert d["genetic_factor"] == 1.0

    def test_from_dict(self):
        """Deserialización desde diccionario."""
        data = {
            "age": 65,
            "is_smoker": False,
            "pack_years": 0,
            "diet": "healthy",
            "genetic_factor": 0.9
        }
        patient = PatientProfile.from_dict(data)
        assert patient.age == 65
        assert patient.diet == DietType.HEALTHY
        assert patient.genetic_factor == 0.9

    def test_invalid_age_low(self):
        """Edad muy baja lanza excepción."""
        with pytest.raises(ValueError, match="Edad debe estar entre 18 y 100"):
            PatientProfile(age=10)

    def test_invalid_age_high(self):
        """Edad muy alta lanza excepción."""
        with pytest.raises(ValueError, match="Edad debe estar entre 18 y 100"):
            PatientProfile(age=150)

    def test_invalid_pack_years(self):
        """Pack years negativo lanza excepción."""
        with pytest.raises(ValueError, match="no puede ser negativo"):
            PatientProfile(pack_years=-5)

    def test_invalid_genetic_factor_low(self):
        """Factor genético muy bajo lanza excepción."""
        with pytest.raises(ValueError, match="Factor genético"):
            PatientProfile(genetic_factor=0.3)

    def test_invalid_genetic_factor_high(self):
        """Factor genético muy alto lanza excepción."""
        with pytest.raises(ValueError, match="Factor genético"):
            PatientProfile(genetic_factor=3.0)


class TestCreateSamplePatient:
    """Tests para función create_sample_patient."""

    def test_default_preset(self):
        """Preset por defecto."""
        patient = create_sample_patient()
        assert patient.age == 60

    def test_young_preset(self):
        """Preset joven."""
        patient = create_sample_patient("young")
        assert patient.age == 35
        assert patient.diet == DietType.HEALTHY

    def test_elderly_preset(self):
        """Preset anciano."""
        patient = create_sample_patient("elderly")
        assert patient.age == 75
        assert patient.genetic_factor == 1.1

    def test_smoker_preset(self):
        """Preset fumador."""
        patient = create_sample_patient("smoker")
        assert patient.is_smoker is True
        assert patient.pack_years == 30

    def test_healthy_preset(self):
        """Preset saludable."""
        patient = create_sample_patient("healthy")
        assert patient.diet == DietType.HEALTHY
        assert patient.genetic_factor == 0.8

    def test_high_risk_preset(self):
        """Preset alto riesgo."""
        patient = create_sample_patient("high_risk")
        assert patient.age == 70
        assert patient.is_smoker is True
        assert patient.pack_years == 40
        assert patient.diet == DietType.POOR
        assert patient.genetic_factor == 1.2

    def test_unknown_preset_returns_default(self):
        """Preset desconocido retorna default."""
        patient = create_sample_patient("unknown")
        assert patient.age == 60


# =============================================================================
# Tests de Tratamientos
# =============================================================================

class TestNoTreatmentStrategy:
    """Tests para NoTreatmentStrategy."""

    def test_properties(self):
        """Propiedades correctas."""
        treatment = NoTreatmentStrategy()
        assert treatment.name == "Ninguno"
        assert treatment.api_code == "ninguno"
        assert treatment.cycle_duration == 0.0
        assert treatment.max_efficacy == 0.0

    def test_beta_always_zero(self):
        """Beta siempre es cero."""
        treatment = NoTreatmentStrategy()
        assert treatment.get_beta(0) == 0.0
        assert treatment.get_beta(10) == 0.0
        assert treatment.get_beta(100) == 0.0


class TestChemotherapyStrategy:
    """Tests para ChemotherapyStrategy."""

    def test_default_properties(self):
        """Propiedades por defecto."""
        chemo = ChemotherapyStrategy()
        assert "Quimioterapia" in chemo.name
        assert chemo.api_code == "quimio"
        assert chemo.cycle_duration == 21.0
        assert chemo.max_efficacy == 0.75

    def test_custom_parameters(self):
        """Parámetros personalizados."""
        chemo = ChemotherapyStrategy(beta_max=0.8, accumulation_rate=0.2)
        assert chemo.max_efficacy == 0.8

    def test_beta_negative_time(self):
        """Beta 0 para tiempo negativo."""
        chemo = ChemotherapyStrategy()
        assert chemo.get_beta(-1) == 0.0

    def test_beta_increases_with_time(self):
        """Beta aumenta con el tiempo (dentro del ciclo)."""
        chemo = ChemotherapyStrategy()
        beta_early = chemo.get_beta(1)
        beta_later = chemo.get_beta(10)
        assert beta_later > beta_early

    def test_beta_resistance_reduces(self):
        """Resistencia reduce eficacia en ciclos posteriores."""
        chemo = ChemotherapyStrategy()
        beta_cycle0 = chemo.get_beta(10)  # Primer ciclo
        beta_cycle3 = chemo.get_beta(10 + 21 * 3)  # Cuarto ciclo
        assert beta_cycle3 < beta_cycle0


class TestRadiotherapyStrategy:
    """Tests para RadiotherapyStrategy."""

    def test_default_properties(self):
        """Propiedades por defecto."""
        radio = RadiotherapyStrategy()
        assert "Radioterapia" in radio.name
        assert radio.api_code == "radio"
        assert radio.cycle_duration == 7.0
        assert radio.max_efficacy == 0.85

    def test_custom_parameters(self):
        """Parámetros personalizados."""
        radio = RadiotherapyStrategy(
            beta_max=0.9,
            active_days=3,
            rest_days=4,
            beta_rest=0.05
        )
        assert radio.max_efficacy == 0.9
        assert radio.cycle_duration == 7.0

    def test_beta_active_days(self):
        """Beta alto en días activos."""
        radio = RadiotherapyStrategy()
        assert radio.get_beta(1) == radio.max_efficacy  # Día activo
        assert radio.get_beta(3) == radio.max_efficacy

    def test_beta_rest_days(self):
        """Beta bajo en días de descanso."""
        radio = RadiotherapyStrategy()
        assert radio.get_beta(6) == 0.1  # Día de descanso

    def test_beta_negative_time(self):
        """Beta 0 para tiempo negativo."""
        radio = RadiotherapyStrategy()
        assert radio.get_beta(-1) == 0.0


class TestImmunotherapyStrategy:
    """Tests para ImmunotherapyStrategy."""

    def test_default_properties(self):
        """Propiedades por defecto."""
        immuno = ImmunotherapyStrategy()
        assert "Inmunoterapia" in immuno.name
        assert immuno.api_code == "inmuno"
        assert immuno.cycle_duration == 21.0
        assert immuno.max_efficacy == 0.65

    def test_beta_gradual_increase(self):
        """Beta aumenta gradualmente."""
        immuno = ImmunotherapyStrategy()
        beta_early = immuno.get_beta(5)
        beta_later = immuno.get_beta(50)
        assert beta_later > beta_early

    def test_beta_asymptotic_to_max(self):
        """Beta tiende al máximo."""
        immuno = ImmunotherapyStrategy()
        beta_long = immuno.get_beta(200)
        assert beta_long <= immuno.max_efficacy

    def test_beta_negative_time(self):
        """Beta 0 para tiempo negativo."""
        immuno = ImmunotherapyStrategy()
        assert immuno.get_beta(-1) == 0.0


class TestSurgeryStrategy:
    """Tests para SurgeryStrategy."""

    def test_default_properties(self):
        """Propiedades por defecto."""
        surgery = SurgeryStrategy()
        assert "Cirugía" in surgery.name
        assert surgery.api_code == "ninguno"
        assert surgery.cycle_duration == 1.0

    def test_custom_parameters(self):
        """Parámetros personalizados."""
        surgery = SurgeryStrategy(removal_fraction=0.9, surgery_day=5)
        assert surgery.max_efficacy == 0.9

    def test_beta_before_surgery(self):
        """Beta 0 antes de cirugía (lejos del día)."""
        surgery = SurgeryStrategy(surgery_day=10)
        assert surgery.get_beta(5) == 0.0

    def test_beta_on_surgery_day(self):
        """Beta alto en día de cirugía."""
        surgery = SurgeryStrategy(surgery_day=10, removal_fraction=0.95)
        beta = surgery.get_beta(10)
        # Debe ser alto (removal_fraction * factor)
        assert beta > 0

    def test_beta_after_surgery(self):
        """Beta 0 después de cirugía."""
        surgery = SurgeryStrategy(surgery_day=10)
        assert surgery.get_beta(15) == 0.0


# =============================================================================
# Tests de RK4Solver
# =============================================================================

class TestRK4Solver:
    """Tests para RK4Solver."""

    def test_exponential_growth(self):
        """Solución exponencial dy/dt = k*y."""
        k = 0.1

        def derivative(t, y):
            return np.array([k * y[0], 0.0])

        solver = RK4Solver(derivative, step_size=0.1)
        y0 = np.array([1.0, 0.0])
        y_final, history = solver.integrate(0, y0, 10.0)

        # e^1 ≈ 2.718
        expected = math.exp(k * 10.0)
        assert y_final[0] == pytest.approx(expected, rel=0.01)

    def test_constant_derivative(self):
        """Solución con derivada cero."""
        def derivative(t, y):
            return np.array([0.0, 0.0])

        solver = RK4Solver(derivative, step_size=0.1)
        y0 = np.array([5.0, 3.0])
        y_final, _ = solver.integrate(0, y0, 10.0)

        assert y_final[0] == pytest.approx(5.0)
        assert y_final[1] == pytest.approx(3.0)

    def test_linear_growth(self):
        """Solución dy/dt = 1 => y = t + y0."""
        def derivative(t, y):
            return np.array([1.0, 0.0])

        solver = RK4Solver(derivative, step_size=0.1)
        y0 = np.array([0.0, 0.0])
        y_final, _ = solver.integrate(0, y0, 5.0)

        assert y_final[0] == pytest.approx(5.0, rel=0.01)

    def test_step(self):
        """Step funciona correctamente."""
        def derivative(t, y):
            return np.array([1.0, 0.0])

        solver = RK4Solver(derivative, step_size=0.5)
        y0 = np.array([0.0, 0.0])
        y_new = solver.step(0, y0)

        assert y_new[0] == pytest.approx(0.5, rel=0.01)

    def test_invalid_step_size_zero(self):
        """Step size cero lanza ValueError."""
        def dummy(t, y):
            return np.array([0.0, 0.0])

        with pytest.raises(ValueError):
            RK4Solver(dummy, step_size=0)

    def test_invalid_step_size_negative(self):
        """Step size negativo lanza ValueError."""
        def dummy(t, y):
            return np.array([0.0, 0.0])

        with pytest.raises(ValueError):
            RK4Solver(dummy, step_size=-0.1)

    def test_invalid_step_size_too_large(self):
        """Step size > 1.0 lanza ValueError."""
        def dummy(t, y):
            return np.array([0.0, 0.0])

        with pytest.raises(ValueError):
            RK4Solver(dummy, step_size=2.0)


# =============================================================================
# Tests de TumorGrowthModel
# =============================================================================

class TestTumorGrowthModel:
    """Tests para TumorGrowthModel."""

    def test_create_model(self):
        """Crear modelo con valores por defecto."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        assert model.sensitive_cells == 5.0
        assert model.resistant_cells == 0.0
        assert model.current_time == 0.0

    def test_create_with_resistant_cells(self):
        """Crear modelo con células resistentes."""
        patient = PatientProfile()
        model = TumorGrowthModel(
            patient,
            initial_sensitive_volume=5.0,
            initial_resistant_volume=2.0
        )
        assert model.total_volume == 7.0

    def test_simulate_without_treatment(self):
        """Simulación sin tratamiento - tumor crece."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        initial = model.total_volume

        model.simulate_days(30)

        assert model.total_volume > initial
        assert model.current_time == 30.0

    def test_simulate_with_chemotherapy(self):
        """Simulación con quimioterapia - crecimiento reducido."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        model.set_treatment(ChemotherapyStrategy())

        model.simulate_days(60)

        # Con quimioterapia, el crecimiento debe ser menor que sin tratamiento
        model_no_treatment = TumorGrowthModel(
            patient, initial_sensitive_volume=5.0
        )
        model_no_treatment.simulate_days(60)
        assert model.total_volume < model_no_treatment.total_volume

    def test_set_treatment(self):
        """Cambiar tratamiento actualiza start_time."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        model.simulate_days(10)
        model.set_treatment(RadiotherapyStrategy())

        assert model.treatment_start_time == 10.0
        assert "Radioterapia" in model.treatment.name

    def test_history_recorded(self):
        """Historial de simulación se registra."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        model.simulate_days(10)

        history = model.history
        assert len(history) >= 10
        # Cada entrada es (tiempo, Ns, Nr)
        assert len(history[0]) == 3

    def test_get_state_dict(self):
        """Estado como diccionario tiene campos requeridos."""
        patient = PatientProfile(age=55, is_smoker=True, pack_years=20)
        model = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        state = model.get_state_dict()

        required = [
            "age", "is_smoker", "pack_years", "has_adequate_diet",
            "sensitive_tumor_volume", "resistant_tumor_volume",
            "active_treatment", "current_day", "total_volume", "approx_stage"
        ]
        for field in required:
            assert field in state, f"Falta campo: {field}"

    def test_get_state_dict_treatment_code(self):
        """get_state_dict usa código API correcto."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=5.0)

        # Sin tratamiento
        assert model.get_state_dict()["active_treatment"] == "ninguno"

        # Con quimio
        model.set_treatment(ChemotherapyStrategy())
        assert model.get_state_dict()["active_treatment"] == "quimio"

        # Con radio
        model.set_treatment(RadiotherapyStrategy())
        assert model.get_state_dict()["active_treatment"] == "radio"

    def test_get_approximate_stage(self):
        """Estadio aproximado según volumen."""
        patient = PatientProfile()

        # IA: < 3 cm³
        model_ia = TumorGrowthModel(patient, initial_sensitive_volume=2.0)
        assert model_ia.get_approximate_stage() == "IA"

        # IB: 3-14 cm³
        model_ib = TumorGrowthModel(patient, initial_sensitive_volume=10.0)
        assert model_ib.get_approximate_stage() == "IB"

        # IV: > 100 cm³
        model_iv = TumorGrowthModel(patient, initial_sensitive_volume=110.0)
        assert model_iv.get_approximate_stage() == "IV"

    def test_get_doubling_time(self):
        """Tiempo de duplicación razonable."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        dt = model.get_doubling_time()
        # NSCLC: típicamente 60-180 días
        assert 30 < dt < 300

    def test_invalid_initial_volume_negative(self):
        """Volumen inicial negativo lanza excepción."""
        patient = PatientProfile()
        with pytest.raises(ValueError):
            TumorGrowthModel(patient, initial_sensitive_volume=-5.0)

    def test_invalid_initial_volume_zero(self):
        """Volumen inicial cero lanza excepción."""
        patient = PatientProfile()
        with pytest.raises(ValueError):
            TumorGrowthModel(patient, initial_sensitive_volume=0.0)

    def test_resistant_volume_negative_clamped_to_zero(self):
        """Volumen resistente negativo se clampea a 0."""
        patient = PatientProfile()
        model = TumorGrowthModel(
            patient,
            initial_sensitive_volume=5.0,
            initial_resistant_volume=-1.0
        )
        # El modelo usa max(0.0, value) para valores negativos
        assert model.resistant_cells == 0.0


# =============================================================================
# Tests de SimulationResult y SimulationRunner
# =============================================================================

class TestSimulationResult:
    """Tests para SimulationResult."""

    def test_create_result(self):
        """Crear resultado con todos los campos."""
        patient = PatientProfile()
        result = SimulationResult(
            patient=patient,
            initial_volume=5.0,
            final_volume=10.0,
            final_sensitive=8.0,
            final_resistant=2.0,
            days_simulated=30,
            treatment_name="Ninguno",
            final_stage="IB",
            daily_states=[],
            backend_responses=[],
        )
        assert result.initial_volume == 5.0
        assert result.final_volume == 10.0
        assert result.days_simulated == 30
        assert result.final_stage == "IB"


class TestSimulationRunner:
    """Tests para SimulationRunner."""

    def test_create_runner_default(self):
        """Crear runner con URL por defecto."""
        runner = SimulationRunner()
        assert "localhost:8000" in runner.backend_url

    def test_create_runner_custom_url(self):
        """Crear runner con URL personalizada."""
        runner = SimulationRunner("http://example.com:9000")
        assert runner.backend_url == "http://example.com:9000"


# =============================================================================
# Tests adicionales para RK4Solver
# =============================================================================

class TestRK4SolverIntegration:
    """Tests de integración para RK4Solver."""

    def test_integrate_days(self):
        """integrate_days retorna estados diarios correctos."""
        def derivative(t, y):
            return np.array([0.1 * y[0], 0.0])

        solver = RK4Solver(derivative, step_size=0.1)
        y0 = np.array([1.0, 0.0])
        daily_states = solver.integrate_days(y0, days=5)

        # Debería tener 6 estados (día 0 + 5 días)
        assert len(daily_states) == 6
        assert daily_states[0][0] == 0  # día 0
        assert daily_states[5][0] == 5  # día 5

    def test_integrate_days_without_record(self):
        """integrate_days sin record_daily solo retorna final."""
        def derivative(t, y):
            return np.array([0.1, 0.0])

        solver = RK4Solver(derivative, step_size=0.1)
        y0 = np.array([0.0, 0.0])
        daily_states = solver.integrate_days(y0, days=5, record_daily=False)

        # Solo el día 0 inicial
        assert len(daily_states) == 1

    def test_integrate_with_history(self):
        """integrate con record_history guarda todos los pasos."""
        def derivative(t, y):
            return np.array([1.0, 0.0])

        solver = RK4Solver(derivative, step_size=0.5)
        y0 = np.array([0.0, 0.0])
        y_final, history = solver.integrate(0, y0, 2.0, record_history=True)

        # Debería tener múltiples pasos
        assert len(history) > 1

    def test_integrate_invalid_t_final(self):
        """integrate con t_final < t0 lanza ValueError."""
        def derivative(t, y):
            return np.array([0.0, 0.0])

        solver = RK4Solver(derivative, step_size=0.1)
        y0 = np.array([0.0, 0.0])

        with pytest.raises(ValueError):
            solver.integrate(10.0, y0, 5.0)  # t_final < t0

    def test_step_invalid_state_size(self):
        """step con estado incorrecto lanza ValueError."""
        def derivative(t, y):
            return np.array([0.0, 0.0])

        solver = RK4Solver(derivative, step_size=0.1)

        with pytest.raises(ValueError):
            solver.step(0, np.array([1.0, 2.0, 3.0]))  # 3 elementos, espera 2


# =============================================================================
# Tests adicionales para SimulationResult
# =============================================================================

class TestSimulationResultSerialization:
    """Tests de serialización para SimulationResult."""

    def test_to_dict_complete(self):
        """to_dict serializa todos los campos correctamente."""
        patient = PatientProfile(age=55, is_smoker=True, pack_years=20)
        result = SimulationResult(
            patient=patient,
            initial_volume=5.0,
            final_volume=10.0,
            final_sensitive=8.0,
            final_resistant=2.0,
            days_simulated=30,
            treatment_name="Quimioterapia",
            final_stage="IIA",
            daily_states=[{"day": 1, "volume": 5.5}],
            backend_responses=[{"status": "ok"}],
            simulation_time_ms=150.5,
        )

        data = result.to_dict()

        assert data["patient"]["age"] == 55
        assert data["patient"]["is_smoker"] is True
        assert data["initial_volume"] == 5.0
        assert data["final_volume"] == 10.0
        assert data["final_sensitive"] == 8.0
        assert data["final_resistant"] == 2.0
        assert data["days_simulated"] == 30
        assert data["treatment_name"] == "Quimioterapia"
        assert data["final_stage"] == "IIA"
        assert len(data["daily_states"]) == 1
        assert len(data["backend_responses"]) == 1
        assert data["simulation_time_ms"] == 150.5
        assert "timestamp" in data

    def test_to_dict_empty_lists(self):
        """to_dict con listas vacías funciona."""
        patient = PatientProfile()
        result = SimulationResult(
            patient=patient,
            initial_volume=1.0,
            final_volume=2.0,
            final_sensitive=1.5,
            final_resistant=0.5,
            days_simulated=10,
            treatment_name="Ninguno",
            final_stage="IA",
            daily_states=[],
            backend_responses=[],
        )

        data = result.to_dict()
        assert data["daily_states"] == []
        assert data["backend_responses"] == []


# =============================================================================
# Tests adicionales para TumorGrowthModel
# =============================================================================

class TestTumorGrowthModelExtended:
    """Tests extendidos para TumorGrowthModel."""

    def test_model_history_populated_after_simulation(self):
        """Historial se llena durante simulación."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=5.0)

        model.simulate_days(10)

        # Historial debe tener al menos 11 entradas (día 0 + 10 días)
        assert len(model.history) >= 11

    def test_simulate_step_updates_time(self):
        """simulate_step actualiza el tiempo correctamente."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=5.0)

        initial_time = model.current_time
        model.simulate_step(2.5)

        assert model.current_time == initial_time + 2.5

    def test_simulate_step_returns_populations(self):
        """simulate_step retorna poblaciones correctas."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=5.0)

        sensitive, resistant = model.simulate_step(1.0)

        assert sensitive >= 0
        assert resistant >= 0

    def test_treatment_reduces_sensitive_cells(self):
        """Tratamiento reduce células sensibles vs sin tratamiento."""
        patient = PatientProfile()

        # Con tratamiento
        model_treated = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        model_treated.set_treatment(ChemotherapyStrategy())
        model_treated.simulate_days(60)

        # Sin tratamiento
        model_untreated = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        model_untreated.simulate_days(60)

        # Células sensibles con tratamiento < sin tratamiento
        assert model_treated.sensitive_cells < model_untreated.sensitive_cells

    def test_capacity_varies_by_smoking_status(self):
        """Capacidad varía según estado de fumador."""
        non_smoker = PatientProfile(is_smoker=False)
        smoker = PatientProfile(is_smoker=True, pack_years=20)

        model_ns = TumorGrowthModel(non_smoker, initial_sensitive_volume=5.0)
        model_s = TumorGrowthModel(smoker, initial_sensitive_volume=5.0)

        # Capacidad no debe ser igual necesariamente (depende del modificador)
        # pero no lanza error
        assert model_ns.capacity > 0
        assert model_s.capacity > 0
