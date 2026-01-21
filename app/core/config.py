"""
Core Configuration - LungCancerVR Backend
Carga variables de entorno y expone configuración centralizada
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración del backend (SOLID: Single Responsibility)"""

    # API Settings
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_title: str = "LungCancerVR AI Teacher API"
    api_version: str = "2.1"

    # Database (PostgreSQL)
    database_url: str = "postgresql+asyncpg://pulmomed:pulmomed_secret@localhost:5432/pulmomed_db"

    # JWT Authentication
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # Vector Database
    chroma_persist_dir: str = "./knowledge_base/embeddings"
    collection_name: str = "medical_knowledge"

    # Embeddings - Modelo multilingüe LIGERO para VR
    # paraphrase-multilingual-MiniLM: ~500MB vs BGE-M3 ~2-4GB
    # Soporta español, suficiente calidad para RAG educativo
    # Alternativa pesada: BAAI/bge-m3 (mejor calidad, 4x más RAM)
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_device: str = "cpu"

    # LLM (Ollama - requiere GPU)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"  # Modelo ligero para VR (3B params)
    ollama_temperature: float = 0.3
    ollama_max_tokens: int = 512  # Reducido para respuestas más rápidas
    ollama_timeout: float = 15.0  # Timeout agresivo para VR

    # RAG Configuration
    retrieval_top_k: int = 5
    chunk_size: int = 512
    chunk_overlap: int = 50
    rerank_distance_threshold: float = 0.7  # Chunks con distancia > esto se filtran

    # Constantes del modelo de simulación (antes hardcodeadas)
    # Usadas en SimulationState.compute_risk_score() y otros
    max_pack_years: float = 150.0  # Máximo pack-years para normalización
    max_tumor_volume: float = 100.0  # Volumen máximo para normalización (cm³)
    min_patient_age: int = 18
    max_patient_age: int = 100

    # Constantes del sistema de historial
    snapshot_size_bytes: int = 100  # Tamaño aproximado de un snapshot
    delta_size_bytes: int = 25  # Tamaño aproximado de un delta

    # Umbrales de estadio tumoral (volumen en cm³)
    stage_ia_max_volume: float = 3.0
    stage_ib_max_volume: float = 14.0
    stage_iia_max_volume: float = 28.0
    stage_iib_max_volume: float = 65.0

    # Development
    debug: bool = True
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """
    Dependency Injection: Retorna instancia singleton de Settings
    Decorador @lru_cache asegura una sola instancia
    """
    return Settings()
