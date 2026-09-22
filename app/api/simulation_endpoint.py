"""Endpoint del modelo tumoral usado por la visualización de Unity."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.schemas.simulation_schemas import (
    LungSimulationFrame,
    LungSimulationRequest,
    LungSimulationResponse,
)
from math_model.patient_profile import DietType, PatientProfile
from math_model.treatments import (
    ChemotherapyStrategy,
    ImmunotherapyStrategy,
    NoTreatmentStrategy,
    RadiotherapyStrategy,
)
from math_model.tumor_growth_model import TumorGrowthModel

router = APIRouter(prefix="/simulation", tags=["Simulación tumoral"])

DIETS = {
    "saludable": DietType.HEALTHY,
    "normal": DietType.NORMAL,
    "mala": DietType.POOR,
}

TREATMENTS = {
    "ninguno": NoTreatmentStrategy,
    "quimio": ChemotherapyStrategy,
    "radio": RadiotherapyStrategy,
    "inmuno": ImmunotherapyStrategy,
}


@router.post(
    "/run",
    response_model=LungSimulationResponse,
    summary="Generar trayectoria de crecimiento tumoral para Unity",
)
async def run_lung_simulation(request: LungSimulationRequest) -> LungSimulationResponse:
    """Ejecuta RK4 en el backend y retorna frames listos para animar en Unity."""
    try:
        patient = PatientProfile(
            age=request.edad,
            is_smoker=request.es_fumador,
            pack_years=request.pack_years,
            diet=DIETS[request.dieta],
            genetic_factor=request.factor_genetico,
        )
        model = TumorGrowthModel(
            patient=patient,
            initial_sensitive_volume=request.volumen_inicial_sensible,
            initial_resistant_volume=request.volumen_inicial_resistente,
        )
        model.set_treatment(TREATMENTS[request.tratamiento]())

        initial_volume = model.total_volume
        frames = [_frame(model, day=0, capacity=model.capacity)]

        for day in range(1, request.dias + 1):
            model.simulate_step(1.0)
            if day % request.intervalo_muestra == 0 or day == request.dias:
                frames.append(_frame(model, day=day, capacity=model.capacity))

        return LungSimulationResponse(
            simulation_id=str(uuid4()),
            modelo="Gompertz polimorfico + RK4",
            dias_simulados=request.dias,
            capacidad_carga=model.capacity,
            volumen_inicial=initial_volume,
            volumen_final=model.total_volume,
            estadio_final=model.get_approximate_stage(),
            frames=frames,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _frame(
    model: TumorGrowthModel,
    day: int,
    capacity: float,
) -> LungSimulationFrame:
    total = model.total_volume
    return LungSimulationFrame(
        dia=day,
        volumen_sensible=model.sensitive_cells,
        volumen_resistente=model.resistant_cells,
        volumen_total=total,
        fraccion_resistente=(model.resistant_cells / total) if total > 0 else 0.0,
        progreso=min(1.0, total / max(capacity, 0.001)),
        estadio=model.get_approximate_stage(),
    )
