"""
API Endpoints - FastAPI Routes
Expone servicios vía REST API (SOLID: Interface Segregation)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import get_settings
from app.models.simulation_state import (
    HealthCheckResponse,
    SimulationState,
    TeacherResponse,
)
from app.repositories.medical_knowledge_repo import get_repository
from app.services.teacher_service import AITeacherService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["AI Teacher"])


@router.post(
    "/consultar_profesor",
    response_model=TeacherResponse,
    summary="Consultar al Profesor IA",
    description="""
    Envía el estado actual de la simulación y recibe feedback educativo personalizado.

    **Pipeline:**
    1. Valida estado de simulación (Pydantic)
    2. Retrieval de conocimiento médico relevante (RAG)
    3. Genera explicación educativa (LLM)
    4. Retorna respuesta estructurada con fuentes

    **Ejemplo de uso desde Unity:**
    ```csharp
    var state = new SimulationState {
        edad = 62,
        es_fumador = true,
        pack_years = 35,
        volumen_tumor_sensible = 12.5f,
        tratamiento_activo = "quimio"
    };
    var response = await client.PostAsync("/api/v1/consultar_profesor", state);
    ```
    """,
)
async def consultar_profesor(
    state: SimulationState,
    service: AITeacherService = Depends(lambda: AITeacherService()),
) -> TeacherResponse:
    """
    Endpoint principal: Recibe estado → Retorna feedback educativo
    """
    try:
        logger.info(
            f"Consulta recibida - Paciente: {state.edad} años, "
            f"Volumen: {state.volumen_total:.2f} cm³"
        )

        response = await service.get_educational_feedback(state)
        return response

    except Exception as e:
        logger.error(f"Error en consulta: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error al generar feedback educativo: {str(e)}"
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Verifica el estado del backend, vector DB, y modelo de embeddings",
)
async def health_check() -> HealthCheckResponse:
    """
    Endpoint de health check para monitoreo
    """
    try:
        settings = get_settings()
        repo = get_repository()
        stats = repo.get_collection_stats()

        return HealthCheckResponse(
            status="healthy",
            version=settings.api_version,
            vector_db_status=f"{stats['status']} ({stats['count']} documentos)",
            embedding_model=settings.embedding_model,
        )

    except Exception as e:
        logger.error(f"Health check falló: {e}")
        raise HTTPException(status_code=503, detail="Servicio no disponible")


@router.get(
    "/casos_biblioteca",
    summary="Listar Casos de Biblioteca",
    description="Retorna lista de casos predefinidos para Modo Biblioteca",
)
async def listar_casos_biblioteca() -> dict:
    """
    Lista casos predefinidos (SEER-based)
    TODO: Implementar cuando se creen los JSONs de casos
    """
    return {
        "casos": [],
        "mensaje": "Funcionalidad de casos de biblioteca en desarrollo",
    }
