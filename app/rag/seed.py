"""Siembra RAG desde casos SEER locales. No requiere PDFs ni transformers."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_LIBRARY = Path("knowledge_base/casos_biblioteca.json")


def library_case_chunks(library_path: str | Path = DEFAULT_LIBRARY) -> list[dict[str, Any]]:
    path = Path(library_path)
    if not path.exists():
        logger.warning("Biblioteca de casos no encontrada: %s", path)
        return []

    with path.open(encoding="utf-8") as handle:
        cases = json.load(handle)

    chunks: list[dict[str, Any]] = []
    for case in cases:
        case_id = case.get("caso_id", "caso")
        title = case.get("titulo", "")
        description = case.get("descripcion", "")
        objectives = case.get("objetivos_aprendizaje") or []
        source = case.get("fuente_estadistica", "")

        if description:
            chunks.append(
                {
                    "text": f"{title}. {description}",
                    "metadata": {
                        "source": case_id,
                        "page": 1,
                        "type": "library_case",
                        "title": title,
                    },
                }
            )
        if objectives:
            chunks.append(
                {
                    "text": (
                        f"Objetivos de aprendizaje — {title}: " + " ".join(objectives)
                    ),
                    "metadata": {
                        "source": case_id,
                        "page": 2,
                        "type": "learning_objectives",
                        "title": title,
                    },
                }
            )
        if source:
            chunks.append(
                {
                    "text": f"Evidencia clínica {title}: {source}",
                    "metadata": {
                        "source": case_id,
                        "page": 3,
                        "type": "seer_nccn",
                        "title": title,
                    },
                }
            )

    return chunks


def seed_library_cases(repository, library_path: str | Path = DEFAULT_LIBRARY) -> int:
    chunks = library_case_chunks(library_path)
    if not chunks:
        return 0

    texts = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    ids = [
        f"{chunk['metadata']['source']}_{chunk['metadata']['type']}_{i}"
        for i, chunk in enumerate(chunks)
    ]
    repository.add_documents(texts=texts, metadatas=metadatas, ids=ids)
    logger.info("Indexados %s chunks desde %s", len(chunks), library_path)
    return len(chunks)
