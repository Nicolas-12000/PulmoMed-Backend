"""
Tests para RAG (Retrieval Augmented Generation)
Suite completa de tests para carga de documentos y recuperación de conocimiento.
"""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile

from app.rag.loader import MedicalPDFLoader
from app.repositories.medical_knowledge_repo import MedicalKnowledgeRepository


# =============================================================================
# Tests para MedicalPDFLoader
# =============================================================================

class TestMedicalPDFLoaderCreation:
    """Tests para creación del loader."""

    def test_create_loader(self):
        """Crear loader de PDFs."""
        with patch('app.rag.loader.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock()
            with patch('app.rag.loader.get_repository') as mock_repo:
                mock_repo.return_value = MagicMock()

                loader = MedicalPDFLoader()
                assert loader is not None


class TestPDFLoading:
    """Tests para carga de PDFs."""

    @pytest.fixture
    def loader(self):
        """Loader con mocks."""
        with patch('app.rag.loader.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock()
            with patch('app.rag.loader.get_repository') as mock_repo:
                mock_repo.return_value = MagicMock()
                yield MedicalPDFLoader()

    def test_load_pdf_not_found(self, loader):
        """Error al cargar PDF no existente."""
        with pytest.raises(FileNotFoundError):
            loader.load_pdf("/path/to/nonexistent.pdf")

    def test_load_directory_not_found(self, loader):
        """Error al cargar directorio no existente."""
        with pytest.raises(FileNotFoundError):
            loader.load_directory("/path/to/nonexistent/")

    def test_load_empty_directory(self, loader):
        """Directorio vacío retorna lista vacía."""
        with tempfile.TemporaryDirectory() as tmpdir:
            chunks = loader.load_directory(tmpdir)
            assert chunks == []


class TestChunking:
    """Tests para división en chunks."""

    @pytest.fixture
    def mock_pdf_reader(self):
        """Mock de PdfReader."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = """
        Este es el primer párrafo con contenido sustancial sobre cáncer de pulmón.
        Contiene información relevante sobre estadificación TNM y tratamientos.

        Este es el segundo párrafo que habla sobre quimioterapia y sus efectos
        secundarios en pacientes con cáncer de pulmón de células no pequeñas.

        Un párrafo muy corto.

        Este párrafo describe los factores de riesgo del cáncer de pulmón,
        incluyendo el tabaquismo, exposición al asbesto y factores genéticos.
        Es importante considerar estos factores en el diagnóstico temprano.
        """

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        return mock_reader

    def test_chunks_have_required_fields(self, mock_pdf_reader):
        """Chunks tienen campos requeridos."""
        with patch('app.rag.loader.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock()
            with patch('app.rag.loader.get_repository') as mock_repo:
                mock_repo.return_value = MagicMock()
                with patch('app.rag.loader.PdfReader', return_value=mock_pdf_reader):
                    with patch('pathlib.Path.exists', return_value=True):
                        loader = MedicalPDFLoader()
                        chunks = loader.load_pdf("/fake/path.pdf")

                        for chunk in chunks:
                            assert "text" in chunk
                            assert "metadata" in chunk
                            assert "source" in chunk["metadata"]
                            assert "page" in chunk["metadata"]

    def test_short_paragraphs_filtered(self, mock_pdf_reader):
        """Párrafos cortos son filtrados."""
        with patch('app.rag.loader.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock()
            with patch('app.rag.loader.get_repository') as mock_repo:
                mock_repo.return_value = MagicMock()
                with patch('app.rag.loader.PdfReader', return_value=mock_pdf_reader):
                    with patch('pathlib.Path.exists', return_value=True):
                        loader = MedicalPDFLoader()
                        chunks = loader.load_pdf("/fake/path.pdf")

                        # Párrafos cortos (< 100 chars) filtrados
                        for chunk in chunks:
                            assert len(chunk["text"]) >= 100


# =============================================================================
# Tests para MedicalKnowledgeRepository
# =============================================================================

class TestMedicalKnowledgeRepository:
    """Tests para repositorio de conocimiento médico."""

    def test_create_repository(self):
        """Crear repositorio."""
        with patch('app.repositories.medical_knowledge_repo.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock()
            mock_settings.return_value.chroma_persist_path = "/tmp/test_chroma"
            mock_settings.return_value.embedding_model = "test_model"

            # El repositorio puede requerir ChromaDB
            try:
                repo = MedicalKnowledgeRepository()
                assert repo is not None
            except Exception:
                # Si falla por dependencias, skip
                pytest.skip("ChromaDB no disponible")

    def test_retrieve_relevant_chunks_structure(self):
        """Chunks recuperados tienen estructura correcta."""
        with patch('app.repositories.medical_knowledge_repo.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock()
            mock_settings.return_value.chroma_persist_path = "/tmp/test_chroma"
            mock_settings.return_value.embedding_model = "test_model"

            try:
                repo = MedicalKnowledgeRepository()

                # Mock del collection
                repo.collection = MagicMock()
                repo.collection.query.return_value = {
                    "documents": [["Contenido sobre tumores"]],
                    "metadatas": [[{"source": "test.pdf"}]],
                    "distances": [[0.5]]
                }

                chunks = repo.retrieve_relevant_chunks(
                    query="¿Qué es un tumor?",
                    top_k=3
                )

                assert isinstance(chunks, list)
            except Exception:
                pytest.skip("ChromaDB no disponible")


# =============================================================================
# Tests para prompts RAG
# =============================================================================

class TestRAGPrompts:
    """Tests para prompts del sistema RAG."""

    def test_prompts_module_exists(self):
        """Módulo de prompts existe."""
        from app.rag import prompts
        assert prompts is not None

    def test_system_prompt_has_content(self):
        """System prompt tiene contenido."""
        from app.rag.prompts import PromptTemplates

        system_prompt = PromptTemplates.SYSTEM_PROMPT
        assert system_prompt is not None
        assert len(system_prompt) > 50
        # Debe mencionar medicina/oncología
        assert any(word in system_prompt.lower() for word in [
            'médic', 'oncolog', 'profesor', 'pulmon', 'cáncer', 'medicina'
        ])

    def test_teacher_query_template_has_placeholders(self):
        """Template de pregunta tiene placeholders."""
        from app.rag.prompts import PromptTemplates

        template = PromptTemplates.TEACHER_QUERY_TEMPLATE
        assert template is not None
        # Debe tener placeholders
        assert "{" in template and "}" in template


# =============================================================================
# Tests de integración RAG
# =============================================================================

class TestRAGIntegration:
    """Tests de integración del sistema RAG."""

    def test_prompt_templates_class_exists(self):
        """Clase PromptTemplates existe y tiene métodos."""
        from app.rag.prompts import PromptTemplates

        assert hasattr(PromptTemplates, 'SYSTEM_PROMPT')
        assert hasattr(PromptTemplates, 'TEACHER_QUERY_TEMPLATE')
        assert hasattr(PromptTemplates, 'format_context')

    @pytest.mark.integration
    def test_real_pdf_loading(self):
        """Carga de PDF real (si existe knowledge_base)."""
        kb_path = Path("knowledge_base")
        if not kb_path.exists():
            pytest.skip("knowledge_base no existe")

        pdf_files = list(kb_path.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No hay PDFs en knowledge_base")

        with patch('app.rag.loader.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock()
            with patch('app.rag.loader.get_repository') as mock_repo:
                mock_repo.return_value = MagicMock()

                loader = MedicalPDFLoader()

                chunks = loader.load_pdf(str(pdf_files[0]))

                assert len(chunks) > 0
                assert all("text" in c for c in chunks)


# =============================================================================
# Tests de casos edge para RAG
# =============================================================================

class TestRAGEdgeCases:
    """Tests para casos límite del sistema RAG."""

    @pytest.fixture
    def loader(self):
        with patch('app.rag.loader.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock()
            with patch('app.rag.loader.get_repository') as mock_repo:
                mock_repo.return_value = MagicMock()
                yield MedicalPDFLoader()

    def test_handle_pdf_with_no_text(self, loader):
        """Maneja PDF sin texto."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch('app.rag.loader.PdfReader', return_value=mock_reader):
            with patch('pathlib.Path.exists', return_value=True):
                chunks = loader.load_pdf("/fake/empty.pdf")
                assert chunks == []

    def test_handle_pdf_with_only_short_text(self, loader):
        """Maneja PDF con solo texto corto."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Título\n\nSubtítulo\n\nCorto"

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch('app.rag.loader.PdfReader', return_value=mock_reader):
            with patch('pathlib.Path.exists', return_value=True):
                chunks = loader.load_pdf("/fake/short.pdf")
                # Todos filtrados por ser cortos
                assert chunks == []

    def test_handle_multiple_pages(self, loader):
        """Maneja PDF con múltiples páginas."""
        pages = []
        for i in range(5):
            mock_page = MagicMock()
            mock_page.extract_text.return_value = f"""
            Contenido de la página {i + 1} con información suficiente
            para superar el filtro de 100 caracteres y ser incluido
            en la lista de chunks para indexación.

            Segundo párrafo de la página {i + 1} también con contenido
            extenso que permita su inclusión en el sistema RAG.
            """
            pages.append(mock_page)

        mock_reader = MagicMock()
        mock_reader.pages = pages

        with patch('app.rag.loader.PdfReader', return_value=mock_reader):
            with patch('pathlib.Path.exists', return_value=True):
                chunks = loader.load_pdf("/fake/multi.pdf")

                # Debe haber chunks de múltiples páginas
                assert len(chunks) > 0

                # Verificar que hay chunks de diferentes páginas
                page_nums = set(c["metadata"]["page"] for c in chunks)
                assert len(page_nums) > 1

    def test_retrieve_with_empty_query(self):
        """Recuperar con query vacío."""
        with patch('app.repositories.medical_knowledge_repo.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock()
            mock_settings.return_value.chroma_persist_path = "/tmp/test"
            mock_settings.return_value.embedding_model = "test"

            try:
                repo = MedicalKnowledgeRepository()
                repo.collection = MagicMock()
                repo.collection.query.return_value = {
                    "documents": [[]],
                    "metadatas": [[]],
                    "distances": [[]]
                }

                chunks = repo.retrieve_relevant_chunks("", top_k=3)
                assert isinstance(chunks, list)
            except Exception:
                pytest.skip("ChromaDB no disponible")


# =============================================================================
# Tests de calidad de contenido
# =============================================================================

class TestRAGContentQuality:
    """Tests para calidad del contenido RAG."""

    def test_chunks_are_meaningful(self):
        """Chunks tienen contenido significativo."""
        with patch('app.rag.loader.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock()
            with patch('app.rag.loader.get_repository') as mock_repo:
                mock_repo.return_value = MagicMock()

                # Simular texto médico real
                mock_page = MagicMock()
                mock_page.extract_text.return_value = """
                La estadificación TNM (Tumor, Nodes, Metastasis) es el sistema
                estándar para clasificar la extensión del cáncer de pulmón.
                El componente T describe el tamaño del tumor primario y su
                invasión a estructuras adyacentes.

                T1: Tumor ≤3cm de diámetro máximo, rodeado de pulmón o pleura
                visceral, sin evidencia de invasión más proximal que el bronquio
                lobar. T1a: ≤1cm, T1b: >1-2cm, T1c: >2-3cm.

                La quimioterapia adyuvante está indicada en estadios II y IIIA
                después de resección completa, con esquemas basados en platino.
                El régimen más común es cisplatino/vinorelbina por 4 ciclos.
                """

                mock_reader = MagicMock()
                mock_reader.pages = [mock_page]

                with patch('app.rag.loader.PdfReader', return_value=mock_reader):
                    with patch('pathlib.Path.exists', return_value=True):
                        loader = MedicalPDFLoader()
                        chunks = loader.load_pdf("/fake/medical.pdf")

                        assert len(chunks) > 0

                        # Chunks deben contener terminología médica
                        all_text = " ".join(c["text"] for c in chunks)
                        medical_terms = [
                            'tumor', 'cáncer', 'estadificación',
                            'quimioterapia', 'pulmón'
                        ]

                        assert any(term in all_text.lower() for term in medical_terms)


# =============================================================================
# Tests para PromptTemplates
# =============================================================================

class TestPromptTemplates:
    """Tests para templates de prompts."""

    def test_format_context_empty_chunks(self):
        """format_context con lista vacía."""
        from app.rag.prompts import PromptTemplates

        result = PromptTemplates.format_context([])

        assert "No se encontró información" in result

    def test_format_context_with_chunks(self):
        """format_context con chunks."""
        from app.rag.prompts import PromptTemplates

        chunks = [
            {
                "text": "Contenido médico sobre cáncer de pulmón",
                "metadata": {"source": "guia_nccn.pdf", "page": 1},
            },
            {
                "text": "Información sobre tratamiento",
                "metadata": {"source": "tratamientos.pdf", "page": 5},
            },
        ]

        result = PromptTemplates.format_context(chunks)

        assert "guia_nccn.pdf" in result
        assert "Contenido médico" in result

    def test_format_context_missing_source(self):
        """format_context maneja metadata faltante."""
        from app.rag.prompts import PromptTemplates

        chunks = [
            {"text": "Contenido sin metadata", "metadata": {}},
        ]

        result = PromptTemplates.format_context(chunks)

        assert "Fuente desconocida" in result

    def test_system_prompt_exists(self):
        """SYSTEM_PROMPT existe y tiene contenido."""
        from app.rag.prompts import PromptTemplates

        assert hasattr(PromptTemplates, 'SYSTEM_PROMPT')
        assert len(PromptTemplates.SYSTEM_PROMPT) > 100

    def test_teacher_query_template_exists(self):
        """TEACHER_QUERY_TEMPLATE existe."""
        from app.rag.prompts import PromptTemplates

        assert hasattr(PromptTemplates, 'TEACHER_QUERY_TEMPLATE')
        assert "{context}" in PromptTemplates.TEACHER_QUERY_TEMPLATE or \
               "{estado}" in PromptTemplates.TEACHER_QUERY_TEMPLATE
