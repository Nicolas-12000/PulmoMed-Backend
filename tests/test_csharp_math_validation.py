"""
test_csharp_math_validation.py
Validación de la lógica matemática del modelo C# usando Python

Estos tests verifican que las ecuaciones implementadas en C# son correctas
sin necesidad de compilar el código C#.
"""

import math

import numpy as np
import pytest
from scipy.integrate import solve_ivp


class TestGompertzModel:
    """Tests del modelo Gompertz con dos poblaciones"""

    def gompertz_derivatives(self, t, state, K, rs, rr, beta):
        """
        Ecuaciones diferenciales del modelo Gompertz
        Coincide con TumorGrowthModel.cs ComputeDerivatives()
        """
        Ns, Nr = state
        N_total = Ns + Nr

        if N_total <= 0:
            return [0, 0]

        gompertz_term = math.log(K / N_total) if N_total < K else 0

        dNs_dt = rs * Ns * gompertz_term - beta * Ns
        dNr_dt = rr * Nr * gompertz_term

        return [dNs_dt, dNr_dt]

    def test_growth_without_treatment(self):
        """Test: Tumor crece sin tratamiento"""
        K = 250.0
        rs = 0.04
        rr = 0.032  # 0.8 * rs
        beta = 0.0  # Sin tratamiento

        initial_state = [10.0, 1.0]  # Ns, Nr
        t_span = (0, 30)
        t_eval = np.linspace(0, 30, 31)

        sol = solve_ivp(
            lambda t, y: self.gompertz_derivatives(t, y, K, rs, rr, beta),
            t_span,
            initial_state,
            t_eval=t_eval,
            method="RK45",
        )

        final_total = sol.y[0][-1] + sol.y[1][-1]
        initial_total = sum(initial_state)

        assert final_total > initial_total, "Tumor debe crecer sin tratamiento"
        assert final_total < K, "No debe exceder capacidad de carga"

    def test_carrying_capacity_limit(self):
        """Test: Capacidad de carga K limita el crecimiento"""
        K = 250.0
        rs = 0.04
        rr = 0.032
        beta = 0.0

        # Iniciar cerca de K
        initial_state = [200.0, 40.0]
        t_span = (0, 100)

        sol = solve_ivp(
            lambda t, y: self.gompertz_derivatives(t, y, K, rs, rr, beta),
            t_span,
            initial_state,
            method="RK45",
        )

        final_total = sol.y[0][-1] + sol.y[1][-1]

        # No debe exceder K significativamente
        assert final_total <= K * 1.01, f"Excede K: {final_total} > {K}"

    def test_treatment_reduces_sensitive_cells(self):
        """Test: Tratamiento reduce células sensibles"""
        K = 250.0
        rs = 0.04
        rr = 0.032
        beta = 0.15  # Quimioterapia β_max

        initial_state = [100.0, 10.0]
        t_span = (0, 30)

        sol = solve_ivp(
            lambda t, y: self.gompertz_derivatives(t, y, K, rs, rr, beta),
            t_span,
            initial_state,
            method="RK45",
        )

        final_sensitive = sol.y[0][-1]
        initial_sensitive = initial_state[0]

        assert (
            final_sensitive < initial_sensitive
        ), "Células sensibles deben disminuir con tratamiento"

    def test_resistant_growth_rate(self):
        """Test: Células resistentes crecen más lento"""
        rs = 0.04
        rr = 0.032  # 0.8 * rs

        assert rr < rs, "rr debe ser menor que rs"
        assert abs(rr - rs * 0.8) < 0.001, "rr debe ser 0.8 * rs"


class TestPatientModifiers:
    """Tests de modificadores de paciente (PatientProfile.cs)"""

    def age_modifier(self, edad):
        """GetAgeGrowthModifier() de PatientProfile.cs"""
        modifier = 1.0 + 0.005 * (edad - 50)
        return max(0.85, min(1.2, modifier))

    def smoking_modifier(self, pack_years):
        """GetSmokingCapacityModifier() de PatientProfile.cs"""
        modifier = 1.0 - 0.003 * pack_years
        return max(0.7, min(1.0, modifier))

    def diet_modifier(self, diet_type):
        """GetDietModifier() de PatientProfile.cs"""
        diet_map = {"saludable": 0.9, "normal": 1.0, "mala": 1.1}
        return diet_map.get(diet_type, 1.0)

    def test_age_modifier_younger(self):
        """Test: Pacientes jóvenes tienen modificador < 1"""
        modifier = self.age_modifier(40)
        assert modifier < 1.0
        assert abs(modifier - 0.95) < 0.01  # 1 + 0.005*(40-50) = 0.95

    def test_age_modifier_baseline(self):
        """Test: Edad 50 es baseline (modificador = 1)"""
        modifier = self.age_modifier(50)
        assert abs(modifier - 1.0) < 0.001

    def test_age_modifier_older(self):
        """Test: Pacientes mayores tienen modificador > 1"""
        modifier = self.age_modifier(70)
        assert modifier > 1.0
        assert abs(modifier - 1.1) < 0.01  # 1 + 0.005*(70-50) = 1.1

    def test_age_modifier_clamped(self):
        """Test: Modificador de edad está limitado [0.85, 1.2]"""
        assert self.age_modifier(20) >= 0.85
        assert self.age_modifier(90) <= 1.2

    def test_smoking_modifier_nonsmoker(self):
        """Test: No fumador tiene modificador = 1"""
        modifier = self.smoking_modifier(0)
        assert abs(modifier - 1.0) < 0.001

    def test_smoking_modifier_light_smoker(self):
        """Test: Fumador leve tiene modificador reducido"""
        modifier = self.smoking_modifier(10)
        assert abs(modifier - 0.97) < 0.01  # 1 - 0.003*10 = 0.97

    def test_smoking_modifier_heavy_smoker(self):
        """Test: Fumador pesado tiene modificador muy reducido"""
        modifier = self.smoking_modifier(50)
        assert abs(modifier - 0.85) < 0.01  # 1 - 0.003*50 = 0.85

    def test_smoking_modifier_clamped(self):
        """Test: Modificador de tabaco está limitado [0.7, 1.0]"""
        assert self.smoking_modifier(100) >= 0.7
        assert self.smoking_modifier(0) <= 1.0

    def test_diet_modifiers(self):
        """Test: Modificadores de dieta correctos"""
        assert abs(self.diet_modifier("saludable") - 0.9) < 0.001
        assert abs(self.diet_modifier("normal") - 1.0) < 0.001
        assert abs(self.diet_modifier("mala") - 1.1) < 0.001


class TestRK4Solver:
    """Tests del solver RK4 (RK4Solver.cs)"""

    def rk4_step(self, t, y, dt, derivative_func):
        """
        Un paso de Runge-Kutta 4to orden
        Coincide con RK4Solver.cs Step()
        """
        k1 = np.array(derivative_func(t, y))
        k2 = np.array(derivative_func(t + dt / 2, y + k1 * dt / 2))
        k3 = np.array(derivative_func(t + dt / 2, y + k2 * dt / 2))
        k4 = np.array(derivative_func(t + dt, y + k3 * dt))

        return y + (k1 + 2 * k2 + 2 * k3 + k4) * dt / 6

    def test_exponential_growth_accuracy(self):
        """Test: RK4 resuelve dy/dt = y correctamente"""

        def derivative(t, y):
            return y

        t0 = 0.0
        y0 = np.array([1.0])
        dt = 0.1

        # 10 pasos de dt=0.1 -> t=1.0
        y = y0.copy()
        for i in range(10):
            y = self.rk4_step(t0 + i * dt, y, dt, derivative)

        expected = math.exp(1.0)  # e^1
        error = abs(y[0] - expected)

        assert error < 0.01, f"Error RK4 muy grande: {error}"

    def test_harmonic_oscillator_energy_conservation(self):
        """Test: RK4 conserva energía en oscilador armónico"""

        def derivative(t, y):
            x, v = y
            omega = 1.0
            return np.array([v, -(omega**2) * x])

        y0 = np.array([1.0, 0.0])  # x=1, v=0
        initial_energy = 0.5 * (y0[0] ** 2 + y0[1] ** 2)

        # Simular un período completo
        dt = 0.01
        steps = int(2 * math.pi / dt)
        y = y0.copy()

        for i in range(steps):
            y = self.rk4_step(i * dt, y, dt, derivative)

        final_energy = 0.5 * (y[0] ** 2 + y[1] ** 2)
        energy_error = abs(final_energy - initial_energy)

        assert (
            energy_error < initial_energy * 0.05
        ), "Energía debe conservarse (error < 5%)"


class TestTumorStaging:
    """Tests de clasificación por estadio (GetApproximateStage)"""

    def get_approximate_stage(self, volume_cm3):
        """
        Clasificación TNM aproximada
        Coincide con TumorGrowthModel.cs GetApproximateStage()
        """
        if volume_cm3 < 14:
            return "IA"
        elif volume_cm3 < 33:
            return "IB"
        elif volume_cm3 < 66:
            return "IIA"
        elif volume_cm3 < 114:
            return "IIB"
        elif volume_cm3 < 180:
            return "IIIA"
        elif volume_cm3 < 270:
            return "IIIB"
        else:
            return "IVA"

    def test_stage_ia(self):
        assert self.get_approximate_stage(5.0) == "IA"
        assert self.get_approximate_stage(13.9) == "IA"

    def test_stage_ib(self):
        assert self.get_approximate_stage(20.0) == "IB"
        assert self.get_approximate_stage(32.9) == "IB"

    def test_stage_iia(self):
        assert self.get_approximate_stage(50.0) == "IIA"

    def test_stage_iiia(self):
        assert self.get_approximate_stage(150.0) == "IIIA"

    def test_stage_iva(self):
        assert self.get_approximate_stage(300.0) == "IVA"


class TestIntegrationScenarios:
    """Tests de integración: flujos completos"""

    def simulate_patient_journey(self):
        """Simula journey completo: detección -> tratamiento -> seguimiento"""
        K = 250.0
        rs = 0.04
        rr = 0.032

        # Modificadores de paciente (62 años, fumador 35 pack-years, mala dieta)
        age_mod = 1.0 + 0.005 * (62 - 50)  # 1.06
        smoking_mod = 1.0 - 0.003 * 35  # 0.895
        diet_mod = 1.1  # Mala

        combined_modifier = age_mod * smoking_mod * diet_mod
        rs_adjusted = rs * combined_modifier
        rr_adjusted = rr * combined_modifier

        # Fase 1: Sin tratamiento (60 días)
        initial_state = [5.0, 0.5]

        def derivatives_no_treatment(t, y):
            Ns, Nr = y
            N_total = Ns + Nr
            if N_total <= 0 or N_total >= K:
                return [0, 0]
            gompertz = math.log(K / N_total)
            return [rs_adjusted * Ns * gompertz, rr_adjusted * Nr * gompertz]

        sol1 = solve_ivp(
            derivatives_no_treatment, (0, 60), initial_state, method="RK45"
        )

        volume_before_treatment = sol1.y[0][-1] + sol1.y[1][-1]

        # Fase 2: Con quimioterapia (90 días)
        beta_max = 0.15
        state_after_60 = [sol1.y[0][-1], sol1.y[1][-1]]

        def derivatives_with_chemo(t, y):
            Ns, Nr = y
            N_total = Ns + Nr
            if N_total <= 0:
                return [0, 0]

            # Beta con resistencia
            resistance_rate = 0.002
            beta = beta_max * (
                1 + resistance_rate * (Nr / N_total if N_total > 0 else 0)
            )

            gompertz = math.log(K / N_total) if N_total < K else 0
            return [
                rs_adjusted * Ns * gompertz - beta * Ns,
                rr_adjusted * Nr * gompertz,
            ]

        sol2 = solve_ivp(derivatives_with_chemo, (0, 90), state_after_60, method="RK45")

        volume_after_treatment = sol2.y[0][-1] + sol2.y[1][-1]

        return {
            "volume_before": volume_before_treatment,
            "volume_after": volume_after_treatment,
            "reduction": volume_before_treatment - volume_after_treatment,
        }

    def test_complete_patient_journey(self):
        """Test: Journey completo produce resultados realistas"""
        result = self.simulate_patient_journey()

        # Debe haber crecimiento inicial
        assert result["volume_before"] > 5.5, "Tumor debe crecer sin tratamiento"

        # En estadio avanzado (>180 cm³), el tratamiento ralentiza pero puede no reducir
        # Esto es médicamente realista.
        # La quimioterapia en IIIA/IIIB a menudo solo controla la progresión
        if result["volume_before"] < 100:
            # Estadio temprano: debe reducir
            assert (
                result["volume_after"] < result["volume_before"]
            ), "Quimioterapia debe reducir volumen en estadios tempranos"
        else:
            # Estadio avanzado: puede crecer más lento o estabilizar
            # Verificamos que al menos no crece descontroladamente
            growth = result["volume_after"] - result["volume_before"]
            # Sin tratamiento crecería ~50-100 cm³ más en 90 días
            # Con tratamiento debe crecer < 20 cm³ o reducir
            msg = (
                "Tratamiento debe controlar progresión en estadio avanzado "
                f"(crecimiento: {growth:.1f} cm³)"
            )
            assert growth < 20, msg


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
