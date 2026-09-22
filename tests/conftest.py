"""Aísla tests del modelo ONNX y de PostgreSQL."""

import os

os.environ["VECTOR_BACKEND"] = "memory"
os.environ["EMBEDDING_BACKEND"] = "hash"
os.environ["EMBEDDING_MODEL"] = "hash-384"
os.environ["EMBEDDING_DIMENSION"] = "384"

from app.core.config import get_settings
from app.repositories.medical_knowledge_repo import reset_repository

get_settings.cache_clear()


def pytest_sessionstart(session):
    get_settings.cache_clear()
    reset_repository()
