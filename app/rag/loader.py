"""
PDF Loader - Indexación de Documentos Médicos
Prepara PDFs de NCCN/SEER para pgvector
"""

import logging
from pathlib import Path
from typing import Dict, List

from pypdf import PdfReader

from app.core.config import get_settings
from app.repositories.medical_knowledge_repo import get_repository

logger = logging.getLogger(__name__)


class MedicalPDFLoader:
    """
    Carga y procesa PDFs médicos para indexación
    Estrategia: Chunking semántico por párrafos
    """

    def __init__(self):
        self.settings = get_settings()
        self.repository = get_repository()

    def load_pdf(self, pdf_path: str) -> List[Dict[str, any]]:
        """
        Carga un PDF y lo divide en chunks

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Lista de dicts con {text, metadata}
        """
        logger.info(f"Cargando PDF: {pdf_path}")

        pdf_path_obj = Path(pdf_path)
        if not pdf_path_obj.exists():
            raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

        reader = PdfReader(pdf_path)
        chunks = []

        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()

            # Dividir por párrafos (doble salto de línea)
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

            for para in paragraphs:
                # Solo chunks con contenido sustancial
                if len(para) > 100:  # Filtrar headers/footers
                    chunks.append(
                        {
                            "text": para,
                            "metadata": {
                                "source": pdf_path_obj.name,
                                "page": page_num,
                                "type": "pdf",
                            },
                        }
                    )

        logger.info(f"Extraídos {len(chunks)} chunks de {pdf_path_obj.name}")
        return chunks

    def load_directory(self, directory_path: str) -> List[Dict[str, any]]:
        """
        Carga todos los PDFs de un directorio

        Args:
            directory_path: Ruta al directorio con PDFs

        Returns:
            Lista consolidada de chunks
        """
        dir_path = Path(directory_path)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directorio no encontrado: {directory_path}")

        all_chunks = []
        pdf_files = list(dir_path.glob("*.pdf"))

        logger.info(f"Encontrados {len(pdf_files)} PDFs en {directory_path}")

        for pdf_file in pdf_files:
            try:
                chunks = self.load_pdf(str(pdf_file))
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Error al cargar {pdf_file}: {e}")

        return all_chunks

    def index_chunks(self, chunks: List[Dict[str, any]]):
        """
        Indexa chunks en el repositorio RAG (RAM + pgvector)

        Args:
            chunks: Lista de dicts con {text, metadata}
        """
        if not chunks:
            logger.warning("No hay chunks para indexar")
            return

        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        ids = [
            f"{chunk['metadata']['source']}_p{chunk['metadata']['page']}_{i}"
            for i, chunk in enumerate(chunks)
        ]

        logger.info("Indexando %s chunks...", len(chunks))
        self.repository.add_documents(texts=texts, metadatas=metadatas, ids=ids)
        logger.info("✅ Indexación completada")


def index_knowledge_base(pdf_directory: str = "./knowledge_base"):
    """
    Script principal para indexar PDFs

    Uso:
        python -m app.rag.loader
    """
    logger.info("=" * 60)
    logger.info("📚 Iniciando indexación de base de conocimiento médico")
    logger.info("=" * 60)

    loader = MedicalPDFLoader()

    try:
        chunks = loader.load_directory(pdf_directory)

        if not chunks:
            logger.warning("⚠️  No se encontraron PDFs o están vacíos")
            logger.info("\n📖 Para añadir PDFs:")
            logger.info("   1. Descarga guías NCCN de: https://www.nccn.org/guidelines")
            logger.info("   2. Colócalas en ./knowledge_base/")
            logger.info("   3. Ejecuta: python -m app.rag.loader")
            return

        loader.index_chunks(chunks)

        stats = loader.repository.get_collection_stats()
        logger.info("\n✅ Base de conocimiento lista:")
        logger.info(f"   - Total documentos: {stats['count']}")
        logger.info(f"   - Modelo embeddings: {loader.settings.embedding_model}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Error en indexación: {e}", exc_info=True)


if __name__ == "__main__":
    index_knowledge_base()
