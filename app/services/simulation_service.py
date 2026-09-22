"""Servicio del modelo Gompertz + RK4 usado por Unity y por /docs."""

from __future__ import annotations

import time
from uuid import uuid4

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
    SurgeryStrategy,
)
from math_model.tumor_growth_model import TumorGrowthModel

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
    "cirugia": SurgeryStrategy,
}


def run_lung_trajectory(request: LungSimulationRequest) -> LungSimulationResponse:
    """Ejecuta RK4 y devuelve frames listos para animar en Unity."""
    started = time.perf_counter()
    diet = DIETS.get(request.dieta)
    treatment_cls = TREATMENTS.get(request.tratamiento)
    if diet is None:
        raise ValueError(f"Dieta no soportada: {request.dieta}")
    if treatment_cls is None:
        raise ValueError(f"Tratamiento no soportado: {request.tratamiento}")

    patient = PatientProfile(
        age=request.edad,
        is_smoker=request.es_fumador,
        pack_years=request.pack_years,
        diet=diet,
        genetic_factor=request.factor_genetico,
    )
    model = TumorGrowthModel(
        patient=patient,
        initial_sensitive_volume=request.volumen_inicial_sensible,
        initial_resistant_volume=request.volumen_inicial_resistente,
    )

    if request.dia_inicio_tratamiento <= 0:
        model.set_treatment(treatment_cls())

    initial_volume = model.total_volume
    frames = [_frame(model, day=0, capacity=model.capacity)]

    for day in range(1, request.dias + 1):
        if request.dia_inicio_tratamiento == day:
            model.set_treatment(treatment_cls())
        model.simulate_step(1.0)
        if day % request.intervalo_muestra == 0 or day == request.dias:
            frames.append(_frame(model, day=day, capacity=model.capacity))

    elapsed_ms = (time.perf_counter() - started) * 1000
    return LungSimulationResponse(
        simulation_id=str(uuid4()),
        modelo="Gompertz polimorfico + RK4",
        dias_simulados=request.dias,
        capacidad_carga=model.capacity,
        volumen_inicial=initial_volume,
        volumen_final=model.total_volume,
        estadio_final=model.get_approximate_stage(),
        tiempo_ms=round(elapsed_ms, 2),
        frames=frames,
    )


def _frame(model: TumorGrowthModel, day: int, capacity: float) -> LungSimulationFrame:
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
