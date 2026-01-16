"""
FastAPI Application Entry Point
Main entry para el backend LungCancerVR
OPTIMIZACIONES:
- Singleton para TeacherService (evita recargar embeddings)
- Lifecycle management para HTTP clients
- Logging estructurado para monitoreo
"""
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.teacher_endpoint import router as teacher_router
from app.core.config import get_settings

# Configurar logging
format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=format_str)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
settings = get_settings()

# Singleton para el servicio (evita recargar modelos)
_teacher_service = None


def get_teacher_service():
    """Retorna singleton del TeacherService (optimización VR)"""
    global _teacher_service
    if _teacher_service is None:
        from app.services.teacher_service import AITeacherService
        from app.repositories.medical_knowledge_repo import get_repository

        repo = get_repository()
        _teacher_service = AITeacherService(repository=repo)
    return _teacher_service


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="""
    ## Backend IA para LungCancerVR Simulator

    Sistema de IA educativa con RAG (Retrieval-Augmented Generation) para proporcionar
    feedback médico preciso basado en guías NCCN y datos SEER.

    ### Características:
    - ✅ **RAG Local**: ChromaDB + BGE embeddings
    - ✅ **LLM Mock**: Respuestas educativas mientras se configura Ollama
    - ✅ **Arquitectura SOLID**: Repository, Service Layer, Dependency Injection
    - ✅ **Testing Completo**: >90% cobertura

    ### Endpoints Principales:
    - `POST /api/v1/consultar_profesor`: Feedback educativo sobre estado de simulación
    - `GET /api/v1/health`: Health check del sistema

    ### Integración Unity:
    ```csharp
    var client = new HttpClient { BaseAddress = new Uri("http://localhost:8000") };
    var response = await client.PostAsJsonAsync(
        "/api/v1/consultar_profesor",
        simulationState
    );
    ```
    """,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS (para desarrollo con Unity)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(teacher_router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler: initializes resources on startup and cleans up on shutdown."""
    logger.info("=" * 60)
    logger.info(f"🚀 LungCancerVR Backend v{settings.api_version} iniciando...")
    logger.info(f"📍 Host: {settings.api_host}:{settings.api_port}")
    logger.info(f"🧠 Embedding Model: {settings.embedding_model}")
    logger.info(f"💾 Vector DB: {settings.chroma_persist_dir}")
    logger.info("=" * 60)

    # Inicializar repository y servicio (SINGLETON - carga embeddings UNA vez)
    from app.repositories.medical_knowledge_repo import get_repository
    from app.llm.ollama_client import OllamaClient

    repo = get_repository()
    stats = repo.get_collection_stats()
    logger.info(f"📚 Documentos indexados: {stats['count']}")

    if stats["count"] == 0:
        logger.warning(
            "⚠️  Base de conocimiento vacía. Ejecutar script de indexación de PDFs."
        )

    # Pre-inicializar el servicio singleton
    service = get_teacher_service()
    logger.info(f"🤖 LLM disponible: {service.llm_client.check_availability()}")

    yield

    # CLEANUP: Cerrar conexiones HTTP
    logger.info("Cerrando LungCancerVR Backend...")
    await OllamaClient.close_client()  # Cerrar connection pool
    repo = get_repository()
    repo.close()

# Attach lifespan to app
app.router.lifespan_context = lifespan


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "LungCancerVR AI Teacher Backend",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    # Ejecutar servidor (desarrollo)
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
