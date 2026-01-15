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
    response_model=dict,
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
            f"Consulta recibida - Paciente: {state.age} años, "
            f"Volumen: {state.total_volume:.2f} cm³"
        )

        response = await service.get_educational_feedback(state)

        # Return a Spanish-keyed dict for backward compatibility with clients/tests
        return {
            "explicacion": response.explanation,
            "recomendacion": response.recommendation,
            "fuentes": response.sources,
            "advertencia": response.warning,
            "retrieved_chunks": response.retrieved_chunks,
            "llm_model": response.llm_model,
            "model_used": response.llm_model,
        }

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
    "/library_cases",
    summary="Listar Casos de Biblioteca",
    description="Retorna lista de casos predefinidos para Modo Biblioteca basados en estadísticas SEER",
    response_model=dict,
)
async def list_library_cases() -> dict:
    """
    Lista casos predefinidos basados en estadísticas SEER.
    Carga los casos desde knowledge_base/casos_biblioteca.json
    """
    import json
    from pathlib import Path

    cases_path = Path(__file__).parent.parent.parent / "knowledge_base" / "casos_biblioteca.json"

    try:
        with open(cases_path, "r", encoding="utf-8") as f:
            cases = json.load(f)
        
        return {
            "count": len(cases),
            "cases": cases,
        }
    except FileNotFoundError:
        logger.error(f"Archivo de casos no encontrado: {cases_path}")
        return {"count": 0, "cases": [], "error": "Archivo de casos no encontrado"}
    except json.JSONDecodeError as e:
        logger.error(f"Error al parsear JSON de casos: {e}")
        return {"count": 0, "cases": [], "error": "Error al parsear archivo de casos"}


@router.get(
    "/library_cases/{case_id}",
    summary="Obtener Caso Específico",
    description="Retorna un caso específico por su ID",
    response_model=dict,
)
async def get_library_case(case_id: str) -> dict:
    """
    Obtiene un caso específico de la biblioteca por su ID.
    """
    import json
    from pathlib import Path

    cases_path = Path(__file__).parent.parent.parent / "knowledge_base" / "casos_biblioteca.json"

    try:
        with open(cases_path, "r", encoding="utf-8") as f:
            cases = json.load(f)
        
        # Buscar el caso por ID
        for case in cases:
            if case.get("caso_id") == case_id:
                return {"found": True, "case": case}
        
        raise HTTPException(status_code=404, detail=f"Caso '{case_id}' no encontrado")
    
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Archivo de casos no encontrado")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error al parsear archivo de casos")
