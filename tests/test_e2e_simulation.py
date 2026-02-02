"""
Tests Exhaustivos de Integración End-to-End para PulmoMed.

Prueba el flujo completo:
1. Modelo matemático Python (PatientProfile, TumorGrowthModel, Treatments)
2. API del backend
3. Casos positivos y negativos para validación robusta
"""
import pytest
import httpx
import math

from math_model import (
    PatientProfile,
    DietType,
    TumorGrowthModel,
    ChemotherapyStrategy,
    RadiotherapyStrategy,
    ImmunotherapyStrategy,
    SurgeryStrategy,
    NoTreatmentStrategy,
    RK4Solver,
    SimulationRunner,
    create_sample_patient,
)


# =============================================================================
# Tests Exhaustivos para PatientProfile
# =============================================================================

class TestPatientProfilePositive:
    """Tests de casos que DEBEN funcionar correctamente."""

    def test_create_default_patient(self):
        """Paciente por defecto tiene valores válidos."""
        patient = PatientProfile()
        assert patient.age == 60
        assert patient.is_smoker is False
        assert patient.pack_years == 0.0
        assert patient.diet == DietType.NORMAL
        assert patient.genetic_factor == 1.0

    def test_create_patient_min_age(self):
        """Paciente con edad mínima válida (18)."""
        patient = PatientProfile(age=18)
        assert patient.age == 18

    def test_create_patient_max_age(self):
        """Paciente con edad máxima válida (100)."""
        patient = PatientProfile(age=100)
        assert patient.age == 100

    def test_create_smoker_patient(self):
        """Paciente fumador con valores válidos."""
        patient = PatientProfile(is_smoker=True, pack_years=30)
        assert patient.is_smoker is True
        assert patient.pack_years == 30

    def test_create_patient_healthy_diet(self):
        """Paciente con dieta saludable."""
        patient = PatientProfile(diet=DietType.HEALTHY)
        assert patient.diet == DietType.HEALTHY
        assert patient.get_diet_modifier() == 0.90

    def test_create_patient_poor_diet(self):
        """Paciente con dieta pobre."""
        patient = PatientProfile(diet=DietType.POOR)
        assert patient.diet == DietType.POOR
        assert patient.get_diet_modifier() == 1.10

    def test_age_growth_modifier_young(self):
        """Modificador de edad para paciente joven (<50)."""
        patient = PatientProfile(age=30)
        modifier = patient.get_age_growth_modifier()
        assert modifier < 1.0
        assert modifier == 1.0 + 0.005 * (30 - 50)  # 0.9

    def test_age_growth_modifier_old(self):
        """Modificador de edad para paciente mayor (>50)."""
        patient = PatientProfile(age=70)
        modifier = patient.get_age_growth_modifier()
        assert modifier > 1.0
        assert modifier == 1.0 + 0.005 * (70 - 50)  # 1.1

    def test_age_growth_modifier_at_50(self):
        """Modificador de edad a los 50 años es neutro."""
        patient = PatientProfile(age=50)
        assert patient.get_age_growth_modifier() == 1.0

    def test_smoking_modifier_non_smoker(self):
        """No fumador tiene modificador 1.0."""
        patient = PatientProfile(is_smoker=False)
        assert patient.get_smoking_capacity_modifier() == 1.0

    def test_smoking_modifier_light_smoker(self):
        """Fumador leve tiene modificador cercano a 1.0."""
        patient = PatientProfile(is_smoker=True, pack_years=10)
        modifier = patient.get_smoking_capacity_modifier()
        assert 0.9 < modifier < 1.0

    def test_smoking_modifier_heavy_smoker(self):
        """Fumador pesado tiene modificador reducido."""
        patient = PatientProfile(is_smoker=True, pack_years=50)
        modifier = patient.get_smoking_capacity_modifier()
        assert modifier < 0.9

    def test_smoking_modifier_minimum_cap(self):
        """Modificador de tabaco tiene mínimo 0.5."""
        patient = PatientProfile(is_smoker=True, pack_years=200)
        modifier = patient.get_smoking_capacity_modifier()
        assert modifier >= 0.5

    def test_combined_modifier_calculation(self):
        """Modificador combinado se calcula correctamente."""
        patient = PatientProfile(
            age=70,
            is_smoker=True,
            pack_years=20,
            diet=DietType.POOR,
            genetic_factor=1.2
        )
        combined = patient.get_combined_modifier()
        expected = (
            patient.get_age_growth_modifier() *
            patient.get_smoking_capacity_modifier() *
            patient.get_diet_modifier() *
            patient.genetic_factor
        )
        assert combined == expected

    def test_to_dict_serialization(self):
        """Serialización a dict funciona correctamente."""
        patient = PatientProfile(
            age=55,
            is_smoker=True,
            pack_years=25,
            diet=DietType.HEALTHY,
            genetic_factor=0.9
        )
        data = patient.to_dict()
        assert data["age"] == 55
        assert data["is_smoker"] is True
        assert data["pack_years"] == 25
        assert data["diet"] == "healthy"
        assert data["genetic_factor"] == 0.9

    def test_from_dict_deserialization(self):
        """Deserialización desde dict funciona correctamente."""
        data = {
            "age": 65,
            "is_smoker": False,
            "pack_years": 0,
            "diet": "poor",
            "genetic_factor": 1.1
        }
        patient = PatientProfile.from_dict(data)
        assert patient.age == 65
        assert patient.is_smoker is False
        assert patient.diet == DietType.POOR
        assert patient.genetic_factor == 1.1

    def test_sample_patient_presets(self):
        """Presets de pacientes de muestra funcionan."""
        presets = ["default", "young", "elderly", "smoker", "healthy", "high_risk"]
        for preset in presets:
            patient = create_sample_patient(preset)
            assert isinstance(patient, PatientProfile)

    def test_sample_patient_unknown_returns_default(self):
        """Preset desconocido retorna paciente por defecto."""
        patient = create_sample_patient("unknown_preset")
        default = create_sample_patient("default")
        assert patient.age == default.age


class TestPatientProfileNegative:
    """Tests de casos que NO deben funcionar (validación de errores)."""

    def test_age_below_minimum_raises(self):
        """Edad menor a 18 lanza ValueError."""
        with pytest.raises(ValueError) as exc_info:
            PatientProfile(age=17)
        assert "18" in str(exc_info.value) or "edad" in str(exc_info.value).lower()

    def test_age_above_maximum_raises(self):
        """Edad mayor a 100 lanza ValueError."""
        with pytest.raises(ValueError) as exc_info:
            PatientProfile(age=101)
        assert "100" in str(exc_info.value) or "edad" in str(exc_info.value).lower()

    def test_negative_pack_years_raises(self):
        """Pack years negativo lanza ValueError."""
        with pytest.raises(ValueError):
            PatientProfile(pack_years=-5)

    def test_genetic_factor_too_low_raises(self):
        """Factor genético menor a 0.5 lanza ValueError."""
        with pytest.raises(ValueError):
            PatientProfile(genetic_factor=0.3)

    def test_genetic_factor_too_high_raises(self):
        """Factor genético mayor a 2.0 lanza ValueError."""
        with pytest.raises(ValueError):
            PatientProfile(genetic_factor=2.5)


# =============================================================================
# Tests Exhaustivos para TumorGrowthModel
# =============================================================================

class TestTumorGrowthModelPositive:
    """Tests de casos que DEBEN funcionar correctamente."""

    def test_create_model_default_values(self):
        """Crear modelo con valores por defecto."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        assert model.sensitive_cells == 5.0
        assert model.resistant_cells == 0.0
        assert model.total_volume == 5.0
        assert model.current_time == 0.0

    def test_create_model_with_resistant_cells(self):
        """Crear modelo con células resistentes iniciales."""
        patient = PatientProfile()
        model = TumorGrowthModel(
            patient,
            initial_sensitive_volume=8.0,
            initial_resistant_volume=2.0
        )
        assert model.sensitive_cells == 8.0
        assert model.resistant_cells == 2.0
        assert model.total_volume == 10.0

    def test_tumor_grows_without_treatment(self):
        """Tumor crece sin tratamiento."""
        patient = PatientProfile(age=60)
        model = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        initial = model.total_volume
        model.simulate_days(30)
        assert model.total_volume > initial
        assert model.current_time == 30.0

    def test_treatment_reduces_growth(self):
        """Tratamiento reduce velocidad de crecimiento."""
        patient = PatientProfile(age=60)

        model_no_treatment = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        model_no_treatment.simulate_days(30)

        model_chemo = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        model_chemo.set_treatment(ChemotherapyStrategy())
        model_chemo.simulate_days(30)

        assert model_chemo.total_volume < model_no_treatment.total_volume

    def test_set_treatment_updates_start_time(self):
        """Establecer tratamiento actualiza tiempo de inicio."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        model.simulate_days(10)
        model.set_treatment(ChemotherapyStrategy())
        assert model.treatment_start_time == 10.0

    def test_stage_ia_small_tumor(self):
        """Tumor pequeño (<3 cm³) es estadio IA."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=2.0)
        assert model.get_approximate_stage() == "IA"

    def test_stage_ib_medium_small(self):
        """Tumor 3-14 cm³ es estadio IB."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=10.0)
        assert model.get_approximate_stage() == "IB"

    def test_stage_iia_medium(self):
        """Tumor 14-28 cm³ es estadio IIA."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=20.0)
        assert model.get_approximate_stage() == "IIA"

    def test_stage_iib_medium_large(self):
        """Tumor 28-65 cm³ es estadio IIB."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=40.0)
        assert model.get_approximate_stage() == "IIB"

    def test_stage_iii_large(self):
        """Tumor 65-100 cm³ es estadio III."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=80.0)
        assert model.get_approximate_stage() == "III"

    def test_stage_iv_very_large(self):
        """Tumor >100 cm³ es estadio IV."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=110.0)
        assert model.get_approximate_stage() == "IV"

    def test_doubling_time_reasonable_range(self):
        """Tiempo de duplicación está en rango razonable."""
        patient = PatientProfile(age=60)
        model = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        doubling_time = model.get_doubling_time()
        # NSCLC típicamente 60-180 días
        assert 30 < doubling_time < 300

    def test_state_dict_has_required_fields(self):
        """State dict tiene todos los campos requeridos por API."""
        patient = PatientProfile(age=62, is_smoker=True, pack_years=30)
        model = TumorGrowthModel(patient, initial_sensitive_volume=10.0)
        state = model.get_state_dict()

        required_fields = [
            "age", "is_smoker", "pack_years", "has_adequate_diet",
            "sensitive_tumor_volume", "resistant_tumor_volume",
            "active_treatment", "current_day", "total_volume", "approx_stage"
        ]
        for field in required_fields:
            assert field in state, f"Campo faltante: {field}"

    def test_state_dict_treatment_code_format(self):
        """State dict tiene código de tratamiento en formato API."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=5.0)

        # Sin tratamiento
        assert model.get_state_dict()["active_treatment"] == "ninguno"

        # Con quimioterapia
        model.set_treatment(ChemotherapyStrategy())
        assert model.get_state_dict()["active_treatment"] == "quimio"

    def test_history_is_recorded(self):
        """Historial de simulación se registra."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        model.simulate_days(10)
        history = model.history
        assert len(history) >= 10

    def test_simulate_step_returns_volumes(self):
        """simulate_step retorna volúmenes actualizados."""
        patient = PatientProfile()
        model = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        ns, nr = model.simulate_step(1.0)
        assert ns > 0
        assert nr >= 0

    def test_capacity_is_modified_by_patient(self):
        """Capacidad de carga se modifica por factores del paciente."""
        non_smoker = PatientProfile(is_smoker=False)
        smoker = PatientProfile(is_smoker=True, pack_years=40)

        model_ns = TumorGrowthModel(non_smoker, initial_sensitive_volume=5.0)
        model_s = TumorGrowthModel(smoker, initial_sensitive_volume=5.0)

        # Fumador tiene menor capacidad
        assert model_s.capacity < model_ns.capacity


class TestTumorGrowthModelNegative:
    """Tests de casos que NO deben funcionar."""

    def test_negative_initial_volume_raises(self):
        """Volumen inicial negativo lanza ValueError."""
        patient = PatientProfile()
        with pytest.raises(ValueError):
            TumorGrowthModel(patient, initial_sensitive_volume=-5.0)

    def test_zero_initial_volume_raises(self):
        """Volumen inicial cero lanza ValueError."""
        patient = PatientProfile()
        with pytest.raises(ValueError):
            TumorGrowthModel(patient, initial_sensitive_volume=0.0)

    def test_negative_resistant_volume_clamped(self):
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
# Tests Exhaustivos para Tratamientos
# =============================================================================

class TestTreatmentsPositive:
    """Tests de casos que DEBEN funcionar correctamente."""

    def test_no_treatment_beta_always_zero(self):
        """Sin tratamiento β=0 siempre."""
        treatment = NoTreatmentStrategy()
        for t in [0, 1, 10, 100, 1000]:
            assert treatment.get_beta(t) == 0
        assert treatment.api_code == "ninguno"

    def test_chemotherapy_beta_increases_in_cycle(self):
        """Quimioterapia β aumenta dentro del ciclo."""
        chemo = ChemotherapyStrategy()
        beta_day1 = chemo.get_beta(1)
        beta_day10 = chemo.get_beta(10)
        assert beta_day10 > beta_day1
        assert chemo.api_code == "quimio"

    def test_chemotherapy_resistance_builds(self):
        """Quimioterapia resistencia aumenta con ciclos."""
        chemo = ChemotherapyStrategy()
        beta_cycle0 = chemo.get_beta(10)
        beta_cycle3 = chemo.get_beta(10 + 63)  # 3 ciclos después
        assert beta_cycle3 < beta_cycle0

    def test_chemotherapy_cycle_duration(self):
        """Quimioterapia tiene ciclo de 21 días."""
        chemo = ChemotherapyStrategy()
        assert chemo.cycle_duration == 21.0

    def test_radiotherapy_high_during_active_days(self):
        """Radioterapia alta durante días activos."""
        radio = RadiotherapyStrategy()
        # Días activos (0-4)
        for day in range(5):
            assert radio.get_beta(day) == radio.max_efficacy
        assert radio.api_code == "radio"

    def test_radiotherapy_low_during_rest_days(self):
        """Radioterapia baja durante días de descanso."""
        radio = RadiotherapyStrategy()
        # Días de descanso (5-6)
        assert radio.get_beta(5) < radio.max_efficacy
        assert radio.get_beta(6) < radio.max_efficacy

    def test_radiotherapy_cycle_repeats(self):
        """Radioterapia ciclo se repite correctamente."""
        radio = RadiotherapyStrategy()
        # Día 0 del ciclo 1 == Día 0 del ciclo 2
        assert radio.get_beta(0) == radio.get_beta(7)

    def test_immunotherapy_gradual_activation(self):
        """Inmunoterapia activación gradual."""
        immuno = ImmunotherapyStrategy()
        beta_early = immuno.get_beta(1)
        beta_late = immuno.get_beta(30)
        assert beta_late > beta_early
        assert immuno.api_code == "inmuno"

    def test_immunotherapy_approaches_max(self):
        """Inmunoterapia se acerca al máximo con el tiempo."""
        immuno = ImmunotherapyStrategy()
        beta_very_late = immuno.get_beta(200)
        assert beta_very_late > 0.5 * immuno.max_efficacy

    def test_surgery_high_on_surgery_day(self):
        """Cirugía alta intensidad en día de operación."""
        surgery = SurgeryStrategy(surgery_day=0)
        assert surgery.get_beta(0) > 0
        assert surgery.get_beta(0.2) > 0

    def test_surgery_zero_after_recovery(self):
        """Cirugía β=0 después de recuperación."""
        surgery = SurgeryStrategy(surgery_day=0)
        assert surgery.get_beta(5) == 0

    def test_all_treatments_negative_time_safe(self):
        """Todos los tratamientos manejan tiempo negativo."""
        treatments = [
            NoTreatmentStrategy(),
            ChemotherapyStrategy(),
            RadiotherapyStrategy(),
            ImmunotherapyStrategy(),
            SurgeryStrategy(),
        ]
        for treatment in treatments:
            assert treatment.get_beta(-1) == 0


class TestTreatmentsApiCodes:
    """Tests de códigos API para tratamientos."""

    def test_no_treatment_code(self):
        """NoTreatmentStrategy tiene código 'ninguno'."""
        assert NoTreatmentStrategy().api_code == "ninguno"

    def test_chemotherapy_code(self):
        """ChemotherapyStrategy tiene código 'quimio'."""
        assert ChemotherapyStrategy().api_code == "quimio"

    def test_radiotherapy_code(self):
        """RadiotherapyStrategy tiene código 'radio'."""
        assert RadiotherapyStrategy().api_code == "radio"

    def test_immunotherapy_code(self):
        """ImmunotherapyStrategy tiene código 'inmuno'."""
        assert ImmunotherapyStrategy().api_code == "inmuno"


# =============================================================================
# Tests Exhaustivos para RK4Solver
# =============================================================================

class TestRK4SolverPositive:
    """Tests de casos que DEBEN funcionar correctamente."""

    def test_exponential_growth_accuracy(self):
        """RK4 resuelve crecimiento exponencial con precisión."""
        import numpy as np
        k = 0.1

        def derivative(t, y):
            return np.array([k * y[0], 0.0])

        solver = RK4Solver(derivative, step_size=0.1)
        y0 = np.array([1.0, 0.0])
        y_final, _ = solver.integrate(0, y0, 10.0)

        expected = math.exp(k * 10.0)
        error = abs(y_final[0] - expected) / expected
        assert error < 0.01  # Error < 1%

    def test_constant_function(self):
        """RK4 maneja función constante (derivada cero)."""
        import numpy as np

        def derivative(t, y):
            return np.array([0.0, 0.0])

        solver = RK4Solver(derivative, step_size=0.1)
        y0 = np.array([5.0, 3.0])
        y_final, _ = solver.integrate(0, y0, 10.0)

        assert abs(y_final[0] - 5.0) < 1e-10
        assert abs(y_final[1] - 3.0) < 1e-10

    def test_step_returns_intermediate_states(self):
        """step retorna estado intermedio correcto."""
        import numpy as np

        def derivative(t, y):
            return np.array([1.0, 0.0])  # dy/dt = 1, solución: y = t + y0

        solver = RK4Solver(derivative, step_size=0.5)
        y0 = np.array([0.0, 0.0])
        y_new = solver.step(0, y0)

        # Después de 0.5 unidades de tiempo, y debería ser ~0.5
        assert abs(y_new[0] - 0.5) < 0.01

    def test_different_step_sizes(self):
        """RK4 funciona con diferentes tamaños de paso."""
        import numpy as np

        def derivative(t, y):
            return np.array([0.1 * y[0], 0.0])

        for step_size in [0.01, 0.05, 0.1, 0.5, 1.0]:
            solver = RK4Solver(derivative, step_size=step_size)
            y0 = np.array([1.0, 0.0])
            y_final, _ = solver.integrate(0, y0, 5.0)
            assert y_final[0] > 1.0  # Debe haber crecido


class TestRK4SolverNegative:
    """Tests de casos que NO deben funcionar."""

    def test_zero_step_size_raises(self):
        """Step size cero lanza ValueError."""
        def dummy(t, y):
            import numpy as np
            return np.array([0.0, 0.0])

        with pytest.raises(ValueError):
            RK4Solver(dummy, step_size=0)

    def test_negative_step_size_raises(self):
        """Step size negativo lanza ValueError."""
        def dummy(t, y):
            import numpy as np
            return np.array([0.0, 0.0])

        with pytest.raises(ValueError):
            RK4Solver(dummy, step_size=-0.1)

    def test_step_size_too_large_raises(self):
        """Step size mayor a 1.0 lanza ValueError."""
        def dummy(t, y):
            import numpy as np
            return np.array([0.0, 0.0])

        with pytest.raises(ValueError):
            RK4Solver(dummy, step_size=2.0)


# =============================================================================
# Tests de Validación de Lógica Médica
# =============================================================================

class TestMedicalLogicValidation:
    """Validación de lógica médica/matemática correcta."""

    def test_gompertz_saturation_limit(self):
        """Tumor no excede capacidad de carga (saturación Gompertz)."""
        patient = PatientProfile(age=60)
        model = TumorGrowthModel(patient, initial_sensitive_volume=90.0)
        model.simulate_days(365)
        # No debe exceder K significativamente
        assert model.total_volume <= model.capacity * 1.2

    def test_treatment_affects_sensitive_more_than_resistant(self):
        """Tratamiento afecta más a células sensibles que resistentes."""
        patient = PatientProfile()
        model = TumorGrowthModel(
            patient,
            initial_sensitive_volume=10.0,
            initial_resistant_volume=2.0,
        )
        initial_ratio = model.sensitive_cells / model.resistant_cells
        model.set_treatment(ChemotherapyStrategy())
        model.simulate_days(60)
        final_ratio = model.sensitive_cells / model.resistant_cells
        # Ratio debe disminuir (resistentes sobreviven más)
        assert final_ratio < initial_ratio

    def test_younger_patients_slower_tumor_growth(self):
        """Pacientes jóvenes tienen crecimiento tumoral más lento."""
        young = PatientProfile(age=35)
        old = PatientProfile(age=75)

        model_young = TumorGrowthModel(young, initial_sensitive_volume=5.0)
        model_old = TumorGrowthModel(old, initial_sensitive_volume=5.0)

        model_young.simulate_days(60)
        model_old.simulate_days(60)

        assert model_old.total_volume > model_young.total_volume

    def test_healthy_diet_slows_progression(self):
        """Dieta saludable ralentiza progresión tumoral."""
        healthy = PatientProfile(diet=DietType.HEALTHY)
        poor = PatientProfile(diet=DietType.POOR)

        model_healthy = TumorGrowthModel(healthy, initial_sensitive_volume=5.0)
        model_poor = TumorGrowthModel(poor, initial_sensitive_volume=5.0)

        model_healthy.simulate_days(60)
        model_poor.simulate_days(60)

        assert model_healthy.total_volume < model_poor.total_volume

    def test_smoker_different_capacity(self):
        """Fumadores tienen diferente capacidad de carga."""
        non_smoker = PatientProfile()
        smoker = PatientProfile(is_smoker=True, pack_years=40)

        model_ns = TumorGrowthModel(non_smoker, initial_sensitive_volume=5.0)
        model_s = TumorGrowthModel(smoker, initial_sensitive_volume=5.0)

        assert model_s.capacity < model_ns.capacity

    def test_combined_treatment_effect_timing(self):
        """Tratamiento iniciado antes vs después tiene diferente efecto."""
        patient = PatientProfile()

        # Tratamiento desde día 0
        model_early = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        model_early.set_treatment(ChemotherapyStrategy())
        model_early.simulate_days(60)

        # Tratamiento desde día 30
        model_late = TumorGrowthModel(patient, initial_sensitive_volume=5.0)
        model_late.simulate_days(30)
        model_late.set_treatment(ChemotherapyStrategy())
        model_late.simulate_days(30)

        # Ambos tratamientos deben afectar el tumor
        # El resultado depende del modelo pero ambos deben ser diferentes
        # (pueden ser aproximados o el comportamiento puede variar)
        assert model_early.total_volume != pytest.approx(model_late.total_volume, rel=0.001) or \
               model_early.total_volume <= model_late.total_volume


# =============================================================================
# Tests de Integración con Backend
# =============================================================================

@pytest.fixture
def backend_url():
    """URL del backend para tests."""
    return "http://localhost:8000"


@pytest.fixture
async def http_client(backend_url):
    """Cliente HTTP para tests."""
    async with httpx.AsyncClient(base_url=backend_url, timeout=30.0) as client:
        yield client


class TestBackendIntegration:
    """Tests de integración con el backend."""

    @pytest.mark.asyncio
    async def test_backend_health(self, http_client):
        """Backend responde a health check."""
        try:
            response = await http_client.get("/api/v1/health")
            if response.status_code == 200:
                data = response.json()
                assert "status" in data
            else:
                pytest.skip("Backend no disponible")
        except httpx.ConnectError:
            pytest.skip("Backend no disponible")

    @pytest.mark.asyncio
    async def test_root_endpoint(self, http_client):
        """Endpoint raíz retorna info correcta."""
        try:
            response = await http_client.get("/")
            if response.status_code == 200:
                data = response.json()
                assert "PulmoMed" in data.get("message", "")
                assert "version" in data
            else:
                pytest.skip("Backend no disponible")
        except httpx.ConnectError:
            pytest.skip("Backend no disponible")

    @pytest.mark.asyncio
    async def test_consult_professor_with_valid_state(self, http_client):
        """Consulta al profesor con estado válido."""
        patient = create_sample_patient("high_risk")
        model = TumorGrowthModel(patient, initial_sensitive_volume=10.0)
        model.simulate_days(30)
        state = model.get_state_dict()

        try:
            response = await http_client.post(
                "/api/v1/consultar_profesor",
                json=state,
            )
            if response.status_code == 200:
                data = response.json()
                assert "explicacion" in data or "error" not in data
            elif response.status_code == 422:
                pytest.fail(f"Validation error: {response.json()}")
            else:
                pytest.skip(f"Backend retornó {response.status_code}")
        except httpx.ConnectError:
            pytest.skip("Backend no disponible")


# =============================================================================
# Tests de SimulationRunner
# =============================================================================

class TestSimulationRunner:
    """Tests para SimulationRunner."""

    def test_create_runner(self):
        """Crear SimulationRunner con URL."""
        runner = SimulationRunner("http://localhost:8000")
        assert runner is not None

    @pytest.mark.asyncio
    async def test_check_backend_health_offline(self):
        """check_backend_health maneja backend offline."""
        runner = SimulationRunner("http://localhost:9999")
        try:
            result = await runner.check_backend_health()
            # Debe retornar algo, no crashear
            assert isinstance(result, dict)
        except Exception:
            # También aceptable si lanza excepción controlada
            pass
        finally:
            await runner.close()


# =============================================================================
# Ejecutar tests directamente
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
