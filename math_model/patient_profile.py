"""
PatientProfile - Perfil del paciente con factores de riesgo
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DietType(Enum):
    """Tipo de dieta del paciente"""
    HEALTHY = "healthy"
    NORMAL = "normal"
    POOR = "poor"


@dataclass
class PatientProfile:
    """
    Perfil clínico del paciente

    Los factores modifican la progresión tumoral según literatura médica:
    - Edad: Afecta tasa de crecimiento (r_s)
    - Tabaquismo: Afecta capacidad de carga (K)
    - Dieta: Modificador general de progresión
    - Genética: Predisposición heredada
    """
    age: int = 60
    is_smoker: bool = False
    pack_years: float = 0.0
    diet: DietType = DietType.NORMAL
    genetic_factor: float = 1.0  # 0.8=baja, 1.0=normal, 1.2=alta

    def __post_init__(self):
        """Validación de datos"""
        if not 18 <= self.age <= 100:
            raise ValueError(f"Edad debe estar entre 18 y 100, got {self.age}")
        if self.pack_years < 0:
            raise ValueError(f"Pack years no puede ser negativo: {self.pack_years}")
        if not 0.5 <= self.genetic_factor <= 2.0:
            raise ValueError(f"Factor genético debe estar entre 0.5 y 2.0: {self.genetic_factor}")

    def get_age_growth_modifier(self) -> float:
        """
        Modificador de tasa de crecimiento basado en edad

        Fórmula: r_s = r_base * (1 + 0.005 * (edad - 50))
        Pacientes mayores tienen tumores ligeramente más agresivos
        """
        return 1.0 + 0.005 * (self.age - 50)

    def get_smoking_capacity_modifier(self) -> float:
        """
        Modificador de capacidad de carga basado en tabaquismo

        Fórmula: K = K_base * (1 - 0.003 * pack_years)
        Tabaquismo reduce capacidad tisular por daño pulmonar
        """
        if not self.is_smoker and self.pack_years == 0:
            return 1.0

        modifier = 1.0 - 0.003 * self.pack_years
        return max(0.5, modifier)  # Mínimo 50% capacidad

    def get_diet_modifier(self) -> float:
        """
        Modificador basado en dieta

        Dieta saludable ralentiza progresión ligeramente
        """
        modifiers = {
            DietType.HEALTHY: 0.90,  # -10% progresión
            DietType.NORMAL: 1.0,
            DietType.POOR: 1.10,     # +10% progresión
        }
        return modifiers.get(self.diet, 1.0)

    def get_combined_modifier(self) -> float:
        """
        Modificador combinado de todos los factores

        Usado para ajustar tasas de crecimiento global
        """
        return (
            self.get_age_growth_modifier() *
            self.get_smoking_capacity_modifier() *
            self.get_diet_modifier() *
            self.genetic_factor
        )

    def to_dict(self) -> dict:
        """Convierte a diccionario para serialización"""
        return {
            "age": self.age,
            "is_smoker": self.is_smoker,
            "pack_years": self.pack_years,
            "diet": self.diet.value,
            "genetic_factor": self.genetic_factor,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PatientProfile":
        """Crea instancia desde diccionario"""
        return cls(
            age=data.get("age", 60),
            is_smoker=data.get("is_smoker", False),
            pack_years=data.get("pack_years", 0.0),
            diet=DietType(data.get("diet", "normal")),
            genetic_factor=data.get("genetic_factor", 1.0),
        )

    def is_valid(self) -> tuple[bool, Optional[str]]:
        """Valida el perfil del paciente"""
        try:
            if not 18 <= self.age <= 100:
                return False, f"Edad inválida: {self.age}"
            if self.pack_years < 0:
                return False, f"Pack years negativo: {self.pack_years}"
            if self.is_smoker and self.pack_years == 0:
                return False, "Fumador sin pack_years"
            return True, None
        except Exception as e:
            return False, str(e)


def create_sample_patient(preset: str = "default") -> PatientProfile:
    """
    Crea pacientes predefinidos para testing

    Args:
        preset: "default", "young", "elderly", "smoker", "healthy", "high_risk"

    Returns:
        PatientProfile configurado
    """
    presets = {
        "default": PatientProfile(age=60),
        "young": PatientProfile(age=35, diet=DietType.HEALTHY),
        "elderly": PatientProfile(age=75, genetic_factor=1.1),
        "smoker": PatientProfile(age=55, is_smoker=True, pack_years=30),
        "healthy": PatientProfile(age=50, diet=DietType.HEALTHY, genetic_factor=0.8),
        "high_risk": PatientProfile(
            age=70,
            is_smoker=True,
            pack_years=40,
            diet=DietType.POOR,
            genetic_factor=1.2
        ),
    }
    return presets.get(preset, presets["default"])
