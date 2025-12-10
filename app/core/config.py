"""
Core Configuration - LungCancerVR Backend
Carga variables de entorno y expone configuración centralizada
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración del backend (SOLID: Single Responsibility)"""
    
    # API Settings
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_title: str = "LungCancerVR AI Teacher API"
    api_version: str = "2.0"
    
    # Vector Database
    chroma_persist_dir: str = "./knowledge_base/embeddings"
    collection_name: str = "medical_knowledge"
    
    # Embeddings
    embedding_model: str = "BAAI/bge-base-en-v1.5"
    embedding_device: str = "cpu"
    
    # LLM (Ollama - futuro)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:70b"
    ollama_temperature: float = 0.3
    ollama_max_tokens: int = 1024
    
    # RAG Configuration
    retrieval_top_k: int = 5
    chunk_size: int = 512
    chunk_overlap: int = 50
    
    # Development
    debug: bool = True
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """
    Dependency Injection: Retorna instancia singleton de Settings
    Decorador @lru_cache asegura una sola instancia
    """
    return Settings()
