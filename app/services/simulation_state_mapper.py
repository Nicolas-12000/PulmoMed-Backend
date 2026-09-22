"""Convierte trayectoria del modelo Gompertz en estado para consultar_profesor."""

from __future__ import annotations

from app.models.simulation_state import SimulationState
from app.schemas.simulation_schemas import LungSimulationFrame, LungSimulationRequest


def teacher_state_from_lung(
    request: LungSimulationRequest,
    frame: LungSimulationFrame,
    *,
    modo: str = "libre",
    caso_id: str | None = None,
    treatment_days: int | None = None,
) -> SimulationState:
    """Misma semántica que Unity PulmoMedSimulationSync."""
    if treatment_days is None:
        if request.tratamiento == "ninguno":
            treatment_days = 0
        elif request.dia_inicio_tratamiento <= frame.dia:
            treatment_days = frame.dia - request.dia_inicio_tratamiento
        else:
            treatment_days = 0

    return SimulationState(
        edad=request.edad,
        es_fumador=request.es_fumador,
        pack_years=request.pack_years,
        dieta=request.dieta,
        volumen_tumor_sensible=frame.volumen_sensible,
        volumen_tumor_resistente=frame.volumen_resistente,
        tratamiento_activo=request.tratamiento,
        dias_tratamiento=max(0, treatment_days),
        modo=modo,
        caso_id=caso_id,
    )
