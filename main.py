"""
FastAPI Application Entry Point
Main entry para el backend PulmoMed
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
from app.api.auth_endpoint import router as auth_router
from app.api.exam_endpoint import router as exam_router
from app.api.stats_endpoint import router as stats_router
from app.api.course_endpoint import router as course_router
from app.api.simulation_endpoint import router as simulation_router
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa DB, RAG y singleton del profesor al arrancar."""
    logger.info("=" * 60)
    logger.info(f"🚀 PulmoMed Backend v{settings.api_version} iniciando...")
    logger.info(f"📍 Host: {settings.api_host}:{settings.api_port}")
    logger.info(f"🧠 Embeddings: {settings.embedding_backend} / {settings.embedding_model}")
    logger.info(f"💾 Vector store: {settings.vector_backend}")
    logger.info("🗄️  Database: PostgreSQL + pgvector")
    logger.info("=" * 60)

    from app.core.database import init_db
    try:
        await init_db()
        logger.info("✅ Base de datos inicializada")
    except Exception as e:
        logger.warning(f"⚠️  No se pudo conectar a PostgreSQL: {e}")
        logger.warning("   Ejecutar: docker-compose up -d postgres")

    from app.repositories.medical_knowledge_repo import get_repository
    from app.llm.ollama_client import OllamaClient

    repo = get_repository()
    hydrated = await repo.hydrate_from_postgres()
    if not hydrated and repo.get_collection_stats()["count"] == 0:
        from app.rag.seed import seed_library_cases

        seeded = seed_library_cases(repo)
        if seeded:
            await repo.persist_to_postgres()
            logger.info("📚 RAG sembrado con %s chunks de casos SEER", seeded)

    stats = repo.get_collection_stats()
    logger.info(f"📚 Documentos indexados: {stats['count']}")

    if stats["count"] == 0:
        logger.warning(
            "⚠️  Base de conocimiento vacía. Ejecutar script de indexación de PDFs."
        )

    service = get_teacher_service()
    logger.info(f"🤖 LLM disponible: {service.llm_client.check_availability()}")

    yield

    logger.info("Cerrando PulmoMed Backend...")
    await OllamaClient.close_client()
    repo = get_repository()
    repo.close()


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan,
    description="""
    ## PulmoMed - Backend IA Educativo

    Sistema de IA educativa con RAG (Retrieval-Augmented Generation) para proporcionar
    feedback médico preciso basado en guías NCCN y datos SEER.

    ### Características:
    - ✅ **RAG Local**: PostgreSQL pgvector + FastEmbed (ONNX)
    - ✅ **LLM Flexible**: Groq (cloud) / Ollama (local)
    - ✅ **Arquitectura SOLID**: Repository, Service Layer, DI
    - ✅ **Autenticación JWT**: OAuth2 con roles
    - ✅ **Exámenes**: Creación y evaluación automática

    ### Endpoints Principales:
    - `POST /api/v1/consultar_profesor`: Feedback educativo IA
    - `POST /api/v1/auth/register`: Registro de usuarios
    - `POST /api/v1/exams/`: Gestión de exámenes
    - `GET /api/v1/health`: Health check del sistema

    ### Integración Unity (VR):
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
app.include_router(auth_router, prefix="/api/v1")
app.include_router(course_router, prefix="/api/v1")  # Cursos antes de exams
app.include_router(exam_router, prefix="/api/v1")
app.include_router(stats_router, prefix="/api/v1")
app.include_router(simulation_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "PulmoMed - Backend IA Educativo",
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
