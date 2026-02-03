"""
Estrategias de Tratamiento - Strategy Pattern
"""
from abc import ABC, abstractmethod
import math


class TreatmentStrategy(ABC):
    """
    Interfaz para estrategias de tratamiento (Strategy Pattern)

    Permite implementar diferentes β(t) (eficacia del tratamiento en el tiempo)
    sin modificar el modelo de crecimiento tumoral

    SOLID: Open/Closed Principle - fácil añadir nuevos tratamientos
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre del tratamiento"""
        pass

    @property
    @abstractmethod
    def api_code(self) -> str:
        """Código para el API: 'ninguno', 'quimio', 'radio', 'inmuno'"""
        pass

    @property
    @abstractmethod
    def cycle_duration(self) -> float:
        """Duración típica del ciclo de tratamiento (días)"""
        pass

    @property
    @abstractmethod
    def max_efficacy(self) -> float:
        """Eficacia máxima del tratamiento (0-1)"""
        pass

    @abstractmethod
    def get_beta(self, time: float) -> float:
        """
        Calcula la intensidad del tratamiento β(t) en el tiempo t

        β(t) representa la tasa de eliminación de células sensibles

        Args:
            time: Tiempo desde inicio del tratamiento (días)

        Returns:
            Intensidad β(t) ∈ [0, 1]
        """
        pass


class NoTreatmentStrategy(TreatmentStrategy):
    """
    Sin tratamiento activo
    β(t) = 0 (sin eliminación de células)
    """

    @property
    def name(self) -> str:
        return "Ninguno"

    @property
    def api_code(self) -> str:
        return "ninguno"

    @property
    def cycle_duration(self) -> float:
        return 0.0

    @property
    def max_efficacy(self) -> float:
        return 0.0

    def get_beta(self, time: float) -> float:
        return 0.0


class ChemotherapyStrategy(TreatmentStrategy):
    """
    Quimioterapia: Cisplatino + Pemetrexed

    β(t) = β_max * (1 - exp(-k*t)) * (1 - 0.1*cycle)

    Modelo: Acumulación gradual + resistencia progresiva
    Basado en: NCCN Guidelines 2024, estudios farmacocinéticos
    """

    def __init__(self, beta_max: float = 0.75, accumulation_rate: float = 0.15):
        self._beta_max = beta_max
        self._k = accumulation_rate
        self._cycle_duration = 21.0  # Ciclos cada 3 semanas

    @property
    def name(self) -> str:
        return "Quimioterapia (Cisplatino + Pemetrexed)"

    @property
    def api_code(self) -> str:
        return "quimio"

    @property
    def cycle_duration(self) -> float:
        return self._cycle_duration

    @property
    def max_efficacy(self) -> float:
        return self._beta_max

    def get_beta(self, time: float) -> float:
        if time < 0:
            return 0.0

        # Ciclo actual (cada 21 días)
        current_cycle = int(time / self._cycle_duration)

        # Tiempo dentro del ciclo actual
        time_in_cycle = time % self._cycle_duration

        # Acumulación exponencial dentro del ciclo
        accumulation = 1.0 - math.exp(-self._k * time_in_cycle)

        # Reducción por resistencia adquirida (10% por ciclo, máx 50%)
        resistance_factor = max(0.5, 1.0 - 0.1 * current_cycle)

        return self._beta_max * accumulation * resistance_factor


class RadiotherapyStrategy(TreatmentStrategy):
    """
    Radioterapia: SBRT (Stereotactic Body Radiation Therapy)

    β(t) = β_max si (t % cycle) < días_activos, sino β_rest

    Modelo: Pulsos de alta intensidad con recuperación
    Basado en: Protocolos RTOG, estudios de fraccionamiento
    """

    def __init__(
        self,
        beta_max: float = 0.85,
        active_days: int = 5,
        rest_days: int = 2,
        beta_rest: float = 0.1
    ):
        self._beta_max = beta_max
        self._active_days = active_days
        self._rest_days = rest_days
        self._beta_rest = beta_rest
        self._cycle_duration = float(active_days + rest_days)

    @property
    def name(self) -> str:
        return "Radioterapia (SBRT)"

    @property
    def api_code(self) -> str:
        return "radio"

    @property
    def cycle_duration(self) -> float:
        return self._cycle_duration

    @property
    def max_efficacy(self) -> float:
        return self._beta_max

    def get_beta(self, time: float) -> float:
        if time < 0:
            return 0.0

        # Posición dentro del ciclo
        time_in_cycle = time % self._cycle_duration

        # Días activos: alta eficacia, días de descanso: baja
        if time_in_cycle < self._active_days:
            return self._beta_max
        else:
            return self._beta_rest


class ImmunotherapyStrategy(TreatmentStrategy):
    """
    Inmunoterapia: Pembrolizumab / Nivolumab

    β(t) = β_max * (1 - exp(-k*t))

    Modelo: Activación gradual del sistema inmune
    Basado en: Estudios KEYNOTE, CheckMate
    """

    def __init__(
        self,
        beta_max: float = 0.65,
        activation_rate: float = 0.08,
        cycle_duration: float = 21.0
    ):
        self._beta_max = beta_max
        self._k = activation_rate
        self._cycle_duration = cycle_duration

    @property
    def name(self) -> str:
        return "Inmunoterapia (Anti-PD1)"

    @property
    def api_code(self) -> str:
        return "inmuno"

    @property
    def cycle_duration(self) -> float:
        return self._cycle_duration

    @property
    def max_efficacy(self) -> float:
        return self._beta_max

    def get_beta(self, time: float) -> float:
        if time < 0:
            return 0.0

        # Activación gradual del sistema inmune
        activation = 1.0 - math.exp(-self._k * time)
        return self._beta_max * activation


class SurgeryStrategy(TreatmentStrategy):
    """
    Cirugía: Resección tumoral

    β(t) = β_max si t < duración, sino 0

    Modelo: Reducción instantánea seguida de potencial recurrencia
    Basado en: Datos de supervivencia post-lobectomía
    """

    def __init__(
        self,
        removal_fraction: float = 0.95,  # % de tumor removido
        surgery_day: float = 0.0
    ):
        self._removal_fraction = removal_fraction
        self._surgery_day = surgery_day

    @property
    def name(self) -> str:
        return f"Cirugía (Resección {self._removal_fraction * 100:.0f}%)"

    @property
    def api_code(self) -> str:
        return "ninguno"  # Cirugía es evento único, luego ninguno

    @property
    def cycle_duration(self) -> float:
        return 1.0  # Evento único

    @property
    def max_efficacy(self) -> float:
        return self._removal_fraction

    def get_beta(self, time: float) -> float:
        # La cirugía aplica una reducción instantánea
        # Se maneja diferente en el modelo (reduce volumen directamente)
        if abs(time - self._surgery_day) < 0.5:  # Día de cirugía
            return self._removal_fraction * 10  # Alta intensidad breve
        return 0.0


# Mapeo de nombres a estrategias
TREATMENT_MAP = {
    "none": NoTreatmentStrategy,
    "chemotherapy": ChemotherapyStrategy,
    "radiotherapy": RadiotherapyStrategy,
    "immunotherapy": ImmunotherapyStrategy,
    "surgery": SurgeryStrategy,
    # Aliases
    "quimioterapia": ChemotherapyStrategy,
    "radioterapia": RadiotherapyStrategy,
    "inmunoterapia": ImmunotherapyStrategy,
    "cirugia": SurgeryStrategy,
}


def get_treatment(name: str, **kwargs) -> TreatmentStrategy:
    """
    Factory function para obtener tratamiento por nombre

    Args:
        name: Nombre del tratamiento (ej: "chemotherapy", "quimioterapia")
        **kwargs: Parámetros adicionales para el constructor

    Returns:
        Instancia de TreatmentStrategy
    """
    name_lower = name.lower().replace(" ", "_")

    if name_lower not in TREATMENT_MAP:
        raise ValueError(f"Tratamiento desconocido: {name}. Opciones: {list(TREATMENT_MAP.keys())}")

    return TREATMENT_MAP[name_lower](**kwargs)
