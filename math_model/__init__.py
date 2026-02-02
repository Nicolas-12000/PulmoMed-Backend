"""
PulmoMed - Modelo Matemático de Crecimiento Tumoral (Python)
============================================================

Equivalente Python del modelo C# para Unity.
Usado para testing end-to-end del backend sin necesidad de Unity.

Ecuaciones de Gompertz polimórficas:
    dNs/dt = rs * Ns * ln(K/(Ns+Nr)) - β(t) * Ns    (Células sensibles)
    dNr/dt = rr * Nr * ln(K/(Ns+Nr))                (Células resistentes)

Fidelidad: >70% según datos SEER/NCCN cuando se calibra correctamente
"""

from .patient_profile import PatientProfile, DietType, create_sample_patient
from .tumor_growth_model import TumorGrowthModel
from .treatments import (
    TreatmentStrategy,
    NoTreatmentStrategy,
    ChemotherapyStrategy,
    RadiotherapyStrategy,
    ImmunotherapyStrategy,
    SurgeryStrategy,
)
from .rk4_solver import RK4Solver
from .simulation import SimulationRunner, SimulationResult

__all__ = [
    "PatientProfile",
    "DietType",
    "create_sample_patient",
    "TumorGrowthModel",
    "TreatmentStrategy",
    "NoTreatmentStrategy",
    "ChemotherapyStrategy",
    "RadiotherapyStrategy",
    "ImmunotherapyStrategy",
    "SurgeryStrategy",
    "RK4Solver",
    "SimulationRunner",
    "SimulationResult",
]
