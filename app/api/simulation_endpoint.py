"""Endpoint del modelo tumoral usado por la visualización de Unity."""

import asyncio

from fastapi import APIRouter, HTTPException

from app.models.simulation_state import SimulationState
from app.schemas.simulation_schemas import LungSimulationRequest, LungSimulationResponse
from app.services.simulation_service import run_lung_trajectory
from app.services.simulation_state_mapper import teacher_state_from_lung

router = APIRouter(prefix="/simulation", tags=["Simulación tumoral"])


@router.post(
    "/run",
    response_model=LungSimulationResponse,
    summary="Generar trayectoria de crecimiento tumoral para Unity",
)
async def run_lung_simulation(request: LungSimulationRequest) -> LungSimulationResponse:
    """Ejecuta RK4 fuera del event loop y retorna frames para animar en Unity."""
    try:
        return await asyncio.to_thread(run_lung_trajectory, request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "/teacher-state",
    response_model=SimulationState,
    response_model_by_alias=True,
    summary="Estado alineado con Gompertz+Rk4 para consultar_profesor",
)
async def lung_teacher_state(request: LungSimulationRequest) -> SimulationState:
    """Re-ejecuta la trayectoria y devuelve el snapshot del último día (misma fuente que /run)."""
    try:
        result = await asyncio.to_thread(run_lung_trajectory, request)
        if not result.frames:
            raise HTTPException(status_code=422, detail="Trayectoria vacía")
        return teacher_state_from_lung(request, result.frames[-1])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
