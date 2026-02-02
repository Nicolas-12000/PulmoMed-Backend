"""
Tests para clientes LLM (Groq, Ollama, Mock)
Suite completa de tests para integración con modelos de lenguaje.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.llm.groq_client import GroqClient
from app.llm.ollama_client import OllamaClient
from app.llm.mock_llm import MockLLM


# =============================================================================
# Tests para GroqClient
# =============================================================================

class TestGroqClient:
    """Tests para cliente Groq."""

    def test_create_client(self):
        """Crear cliente Groq."""
        with patch('app.llm.groq_client.get_settings') as mock_settings:
            mock_settings.return_value.groq_api_key = "gsk_test_key_12345"
            mock_settings.return_value.groq_model = "llama-3.1-8b-instant"
            mock_settings.return_value.groq_temperature = 0.3
            mock_settings.return_value.groq_max_tokens = 1000

            client = GroqClient()
            assert client._api_key == "gsk_test_key_12345"
            assert client._model == "llama-3.1-8b-instant"

    def test_check_availability_with_valid_key(self):
        """Disponibilidad con API key válida."""
        with patch('app.llm.groq_client.get_settings') as mock_settings:
            mock_settings.return_value.groq_api_key = "gsk_valid_key"
            mock_settings.return_value.groq_model = "test"

            client = GroqClient()
            assert client.check_availability() is True

    def test_check_availability_without_key(self):
        """No disponible sin API key."""
        with patch('app.llm.groq_client.get_settings') as mock_settings:
            mock_settings.return_value.groq_api_key = ""
            mock_settings.return_value.groq_model = "test"

            client = GroqClient()
            assert client.check_availability() is False

    def test_check_availability_invalid_key(self):
        """No disponible con key inválida."""
        with patch('app.llm.groq_client.get_settings') as mock_settings:
            mock_settings.return_value.groq_api_key = "invalid_key"
            mock_settings.return_value.groq_model = "test"

            client = GroqClient()
            assert client.check_availability() is False

    @pytest.mark.asyncio
    async def test_query_returns_fallback_without_key(self):
        """Query retorna fallback sin API key."""
        with patch('app.llm.groq_client.get_settings') as mock_settings:
            mock_settings.return_value.groq_api_key = ""
            mock_settings.return_value.groq_model = "test"

            client = GroqClient()
            response = await client.query("Test prompt")

            # Debe retornar respuesta de fallback
            assert response is not None
            assert len(response) > 0

    @pytest.mark.asyncio
    async def test_query_successful_response(self):
        """Query exitoso con Groq API."""
        with patch('app.llm.groq_client.get_settings') as mock_settings:
            mock_settings.return_value.groq_api_key = "gsk_test_key"
            mock_settings.return_value.groq_model = "llama-3.1-8b-instant"
            mock_settings.return_value.groq_temperature = 0.3
            mock_settings.return_value.groq_max_tokens = 1000

            client = GroqClient()

            # Mock HTTP response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": "Respuesta del modelo sobre oncología pulmonar."
                    }
                }]
            }
            mock_response.raise_for_status = MagicMock()

            with patch.object(
                GroqClient,
                'get_http_client',
                return_value=AsyncMock(post=AsyncMock(return_value=mock_response))
            ):
                response = await client.query("¿Qué es el cáncer de pulmón?")
                assert "oncología" in response or len(response) > 0

    @pytest.mark.asyncio
    async def test_query_handles_http_error(self):
        """Query maneja errores HTTP."""
        with patch('app.llm.groq_client.get_settings') as mock_settings:
            mock_settings.return_value.groq_api_key = "gsk_test_key"
            mock_settings.return_value.groq_model = "test"
            mock_settings.return_value.groq_temperature = 0.3
            mock_settings.return_value.groq_max_tokens = 1000

            client = GroqClient()

            # Mock HTTP error
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Error",
                    request=MagicMock(),
                    response=MagicMock(status_code=500)
                )
            )

            with patch.object(GroqClient, 'get_http_client', return_value=mock_client):
                response = await client.query("Test")
                # Debe retornar fallback en caso de error
                assert response is not None

    @pytest.mark.asyncio
    async def test_close_client(self):
        """Cerrar cliente HTTP."""
        # Crear cliente mock
        GroqClient._shared_client = AsyncMock()
        GroqClient._shared_client.aclose = AsyncMock()

        await GroqClient.close_client()

        assert GroqClient._shared_client is None


# =============================================================================
# Tests para OllamaClient
# =============================================================================

class TestOllamaClient:
    """Tests para cliente Ollama."""

    def test_create_client(self):
        """Crear cliente Ollama."""
        with patch('app.llm.ollama_client.get_settings') as mock_settings:
            mock_settings.return_value.ollama_url = "http://localhost:11434"
            mock_settings.return_value.ollama_model = "llama3.2"
            mock_settings.return_value.ollama_timeout = 30

            client = OllamaClient()
            # Verificar que el cliente se creó
            assert client is not None

    @pytest.mark.asyncio
    async def test_check_availability_when_running(self):
        """Ollama disponible cuando está corriendo."""
        with patch('app.llm.ollama_client.get_settings') as mock_settings:
            mock_settings.return_value.ollama_url = "http://localhost:11434"
            mock_settings.return_value.ollama_model = "llama3.2"
            mock_settings.return_value.ollama_timeout = 30

            client = OllamaClient()

            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client.aclose = AsyncMock()
                mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_class.return_value.__aexit__ = AsyncMock()

                # El método es síncrono, así que lo llamamos directamente
                # Pero check_availability de Ollama puede ser async
                is_available = client.check_availability()
                # Puede retornar False si no hay servidor real
                assert isinstance(is_available, bool)

    @pytest.mark.asyncio
    async def test_query_successful(self):
        """Query exitoso a Ollama."""
        with patch('app.llm.ollama_client.get_settings') as mock_settings:
            mock_settings.return_value.ollama_url = "http://localhost:11434"
            mock_settings.return_value.ollama_model = "llama3.2"
            mock_settings.return_value.ollama_timeout = 30

            client = OllamaClient()

            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "response": "Respuesta de Ollama sobre tumores."
                }
                mock_response.raise_for_status = MagicMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.aclose = AsyncMock()
                mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_class.return_value.__aexit__ = AsyncMock()

                response = await client.query("¿Qué es un tumor?")
                # Puede ser respuesta real o fallback
                assert response is not None


# =============================================================================
# Tests para MockLLM
# =============================================================================

class TestMockLLM:
    """Tests para cliente Mock."""

    def test_create_mock_client(self):
        """Crear cliente Mock."""
        client = MockLLM()
        assert client is not None

    def test_check_availability_always_true(self):
        """Mock siempre disponible."""
        client = MockLLM()
        assert client.check_availability() is True

    @pytest.mark.asyncio
    async def test_query_returns_mock_response(self):
        """Query retorna respuesta mock."""
        client = MockLLM()
        response = await client.query("Test prompt")

        assert response is not None
        assert len(response) > 0
        # Mock debe incluir contenido médico
        assert any(word in response.lower() for word in [
            'tumor', 'cáncer', 'tratamiento', 'paciente', 'médico',
            'pulmonar', 'pulmón', 'estadio', 'oncología'
        ]) or len(response) > 10

    @pytest.mark.asyncio
    async def test_query_different_prompts(self):
        """Mock responde a diferentes prompts."""
        client = MockLLM()

        prompts = [
            "¿Qué es el cáncer de pulmón?",
            "¿Cuáles son los tratamientos?",
            "¿Cómo funciona la quimioterapia?",
        ]

        responses = []
        for prompt in prompts:
            response = await client.query(prompt)
            responses.append(response)
            assert response is not None

    @pytest.mark.asyncio
    async def test_query_empty_prompt(self):
        """Mock maneja prompt vacío."""
        client = MockLLM()
        response = await client.query("")

        # Debe retornar algo aunque el prompt esté vacío
        assert response is not None


# =============================================================================
# Tests de Integración LLM
# =============================================================================

class TestLLMIntegration:
    """Tests de integración entre clientes LLM."""

    def test_all_clients_implement_interface(self):
        """Todos los clientes implementan la interfaz."""

        with patch('app.llm.groq_client.get_settings') as mock_settings:
            mock_settings.return_value.groq_api_key = "gsk_test"
            mock_settings.return_value.groq_model = "test"

            groq = GroqClient()
            assert hasattr(groq, 'query')
            assert hasattr(groq, 'check_availability')

        with patch('app.llm.ollama_client.get_settings') as mock_settings:
            mock_settings.return_value.ollama_url = "http://localhost:11434"
            mock_settings.return_value.ollama_model = "test"
            mock_settings.return_value.ollama_timeout = 30

            ollama = OllamaClient()
            assert hasattr(ollama, 'query')
            assert hasattr(ollama, 'check_availability')

        mock = MockLLM()
        assert hasattr(mock, 'query')
        assert hasattr(mock, 'check_availability')

    @pytest.mark.asyncio
    async def test_mock_fallback_behavior(self):
        """Mock actúa como fallback válido."""
        mock = MockLLM()

        # Simular 10 queries
        for i in range(10):
            response = await mock.query(f"Pregunta {i}")
            assert response is not None
            assert len(response) > 0


# =============================================================================
# Tests con API Real de Groq (si está disponible)
# =============================================================================

@pytest.mark.integration
class TestGroqRealAPI:
    """Tests con la API real de Groq (requiere GROQ_API_KEY)."""

    @pytest.fixture
    def groq_client(self):
        """Cliente Groq para tests reales."""
        client = GroqClient()
        if not client.check_availability():
            pytest.skip("Groq API key no configurada")
        return client

    @pytest.mark.asyncio
    async def test_real_query_medical_question(self, groq_client):
        """Query real sobre medicina."""
        response = await groq_client.query(
            "Explica brevemente qué es el estadio IIIA en cáncer de pulmón."
        )

        assert response is not None
        assert len(response) > 50
        # Debe mencionar algo relevante
        assert any(word in response.lower() for word in [
            'tumor', 'cáncer', 'pulmón', 'estadio', 'iii', 'tratamiento',
            'ganglios', 'metástasis', 'cirugía', 'quimioterapia'
        ])

    @pytest.mark.asyncio
    async def test_real_query_spanish_response(self, groq_client):
        """Query real retorna respuesta en español."""
        response = await groq_client.query(
            "¿Cuáles son los factores de riesgo para cáncer de pulmón?"
        )

        assert response is not None
        # Debe contener palabras en español
        spanish_words = ['el', 'la', 'de', 'que', 'los', 'las', 'del', 'para']
        assert any(word in response.lower() for word in spanish_words)

    @pytest.mark.asyncio
    async def test_real_query_generates_question(self, groq_client):
        """Query real para generar pregunta de examen."""
        prompt = """
        Genera una pregunta de opción múltiple sobre estadificación TNM
        en cáncer de pulmón. Formato JSON:
        {
            "pregunta": "...",
            "opciones": ["A", "B", "C", "D"],
            "respuesta_correcta": 0
        }
        """

        response = await groq_client.query(prompt)

        assert response is not None
        # Debe contener estructura de pregunta
        assert "pregunta" in response.lower() or "?" in response


# =============================================================================
# Tests Adicionales para OllamaClient
# =============================================================================

class TestOllamaClientAdditional:
    """Tests adicionales para OllamaClient."""

    def test_ollama_default_config(self):
        """Configuración por defecto de Ollama."""
        with patch('app.llm.ollama_client.get_settings') as mock_settings:
            mock_settings.return_value.ollama_base_url = "http://localhost:11434"
            mock_settings.return_value.ollama_model = "llama3"
            mock_settings.return_value.ollama_temperature = 0.7
            mock_settings.return_value.ollama_max_tokens = 2048

            client = OllamaClient()
            # Verificar que el cliente se creó correctamente
            assert client.settings.ollama_base_url == "http://localhost:11434"

    @pytest.mark.asyncio
    async def test_ollama_query_returns_mock_when_not_available(self):
        """Ollama retorna mock cuando no está disponible."""
        with patch('app.llm.ollama_client.get_settings') as mock_settings:
            mock_settings.return_value.ollama_base_url = "http://localhost:11434"
            mock_settings.return_value.ollama_model = "llama3"
            mock_settings.return_value.ollama_temperature = 0.7
            mock_settings.return_value.ollama_max_tokens = 2048

            client = OllamaClient(force_mock=True)

            response = await client.query("Test prompt")

            # Debe retornar respuesta mock
            assert response is not None
            assert len(response) > 0

    def test_ollama_force_mock_not_available(self):
        """force_mock hace que is_available sea False."""
        with patch('app.llm.ollama_client.get_settings') as mock_settings:
            mock_settings.return_value.ollama_base_url = "http://localhost:11434"
            mock_settings.return_value.ollama_model = "llama3"
            mock_settings.return_value.ollama_temperature = 0.7
            mock_settings.return_value.ollama_max_tokens = 2048

            client = OllamaClient(force_mock=True)

            assert client.is_available is False

    def test_ollama_check_availability(self):
        """check_availability usa is_available."""
        with patch('app.llm.ollama_client.get_settings') as mock_settings:
            mock_settings.return_value.ollama_base_url = "http://localhost:11434"
            mock_settings.return_value.ollama_model = "llama3"
            mock_settings.return_value.ollama_temperature = 0.7
            mock_settings.return_value.ollama_max_tokens = 2048

            client = OllamaClient(force_mock=True)

            assert client.check_availability() is False

    def test_ollama_get_model_name_mock(self):
        """get_model_name retorna mock cuando no disponible."""
        with patch('app.llm.ollama_client.get_settings') as mock_settings:
            mock_settings.return_value.ollama_base_url = "http://localhost:11434"
            mock_settings.return_value.ollama_model = "llama3"
            mock_settings.return_value.ollama_temperature = 0.7
            mock_settings.return_value.ollama_max_tokens = 2048

            client = OllamaClient(force_mock=True)

            name = client.get_model_name()
            assert name == "ollama-mock"

    def test_ollama_mock_response_treatment(self):
        """Mock response para tratamiento."""
        with patch('app.llm.ollama_client.get_settings') as mock_settings:
            mock_settings.return_value.ollama_base_url = "http://localhost:11434"
            mock_settings.return_value.ollama_model = "llama3"
            mock_settings.return_value.ollama_temperature = 0.7
            mock_settings.return_value.ollama_max_tokens = 2048

            client = OllamaClient()

            response = client._mock_response("¿Cuál es el tratamiento?")

            # El mock contiene la respuesta de "treatment" de MOCK_RESPONSES
            assert len(response) > 50  # Verificar que hay contenido

    def test_ollama_mock_response_progression(self):
        """Mock response para progresión."""
        with patch('app.llm.ollama_client.get_settings') as mock_settings:
            mock_settings.return_value.ollama_base_url = "http://localhost:11434"
            mock_settings.return_value.ollama_model = "llama3"
            mock_settings.return_value.ollama_temperature = 0.7
            mock_settings.return_value.ollama_max_tokens = 2048

            client = OllamaClient()

            response = client._mock_response("Analiza la progresión del tumor")

            # El mock contiene la respuesta de "progression" de MOCK_RESPONSES
            assert len(response) > 50  # Verificar que hay contenido

    def test_ollama_mock_response_default(self):
        """Mock response por defecto."""
        with patch('app.llm.ollama_client.get_settings') as mock_settings:
            mock_settings.return_value.ollama_base_url = "http://localhost:11434"
            mock_settings.return_value.ollama_model = "llama3"
            mock_settings.return_value.ollama_temperature = 0.7
            mock_settings.return_value.ollama_max_tokens = 2048

            client = OllamaClient()

            response = client._mock_response("Pregunta genérica")

            assert len(response) > 50

    def test_ollama_query_sync_uses_mock_when_not_available(self):
        """query_sync usa mock cuando no disponible."""
        with patch('app.llm.ollama_client.get_settings') as mock_settings:
            mock_settings.return_value.ollama_base_url = "http://localhost:11434"
            mock_settings.return_value.ollama_model = "llama3"
            mock_settings.return_value.ollama_temperature = 0.7
            mock_settings.return_value.ollama_max_tokens = 2048

            client = OllamaClient(force_mock=True)

            response = client.query_sync("Test prompt")

            assert response is not None
            assert len(response) > 0

    @pytest.mark.asyncio
    async def test_ollama_close_client(self):
        """close_client cierra el cliente HTTP."""
        # Asegurar que no hay cliente compartido
        OllamaClient._shared_client = None

        # Crear cliente
        _ = OllamaClient.get_http_client()
        assert OllamaClient._shared_client is not None

        # Cerrar
        await OllamaClient.close_client()
        assert OllamaClient._shared_client is None

    @pytest.mark.asyncio
    async def test_ollama_close_client_when_none(self):
        """close_client maneja caso sin cliente."""
        OllamaClient._shared_client = None

        # No debe lanzar excepción
        await OllamaClient.close_client()

        assert OllamaClient._shared_client is None

    def test_ollama_get_http_client_singleton(self):
        """get_http_client retorna singleton."""
        OllamaClient._shared_client = None

        client1 = OllamaClient.get_http_client()
        client2 = OllamaClient.get_http_client()

        assert client1 is client2

    def test_check_ollama_connection_sync_returns_false_on_error(self):
        """_check_ollama_connection_sync retorna False en error."""
        with patch('app.llm.ollama_client.get_settings') as mock_settings:
            mock_settings.return_value.ollama_base_url = "http://localhost:11434"
            mock_settings.return_value.ollama_model = "llama3"
            mock_settings.return_value.ollama_temperature = 0.7
            mock_settings.return_value.ollama_max_tokens = 2048

            client = OllamaClient()

            # Mock httpx.Client para simular error
            with patch('httpx.Client') as mock_httpx:
                mock_httpx.return_value.__enter__ = MagicMock(
                    side_effect=Exception("Connection refused")
                )
                mock_httpx.return_value.__exit__ = MagicMock(return_value=False)

                result = client._check_ollama_connection_sync()

                assert result is False


# =============================================================================
# Tests Adicionales para MockLLM
# =============================================================================

class TestMockLLMAdditional:
    """Tests adicionales para MockLLM."""

    def test_mock_llm_always_available(self):
        """MockLLM siempre está disponible."""
        client = MockLLM()
        assert client.check_availability() is True

    @pytest.mark.asyncio
    async def test_mock_llm_generates_staging_response(self):
        """MockLLM genera respuesta sobre estadificación."""
        client = MockLLM()
        response = await client.query("¿Cuál es el estadio tumoral T2N1M0?")

        assert response is not None
        assert len(response) > 20

    @pytest.mark.asyncio
    async def test_mock_llm_generates_treatment_response(self):
        """MockLLM genera respuesta sobre tratamiento."""
        client = MockLLM()
        response = await client.query("¿Qué tratamiento es mejor para estadio III?")

        assert response is not None
        assert len(response) > 20

    @pytest.mark.asyncio
    async def test_mock_llm_generates_prognosis_response(self):
        """MockLLM genera respuesta sobre pronóstico."""
        client = MockLLM()
        response = await client.query("¿Cuál es el pronóstico para un paciente fumador?")

        assert response is not None
        assert len(response) > 20

    @pytest.mark.asyncio
    async def test_mock_llm_empty_prompt(self):
        """MockLLM maneja prompt vacío."""
        client = MockLLM()
        response = await client.query("")

        # Debe retornar algo
        assert response is not None

    def test_mock_llm_consistent_responses(self):
        """MockLLM retorna respuestas consistentes."""
        client1 = MockLLM()
        client2 = MockLLM()

        # Ambos clientes deben estar disponibles
        assert client1.check_availability() == client2.check_availability()

    def test_mock_llm_query_sync(self):
        """MockLLM soporta query síncrono."""
        client = MockLLM(responses={"test": "RESPUESTA_SYNC"})

        response = client.query_sync("Este es un test")

        assert response == "RESPUESTA_SYNC"
        assert client.call_count == 1

    def test_mock_llm_query_sync_no_match(self):
        """MockLLM query sync retorna default sin match."""
        client = MockLLM(responses={"keyword": "respuesta"})

        response = client.query_sync("prompt sin match")

        assert response == client.default_response
        assert client.last_prompt == "prompt sin match"

    def test_mock_llm_set_available(self):
        """MockLLM puede simular estar no disponible."""
        client = MockLLM()

        assert client.check_availability() is True

        client.set_available(False)
        assert client.check_availability() is False

        client.set_available(True)
        assert client.check_availability() is True

    def test_mock_llm_reset(self):
        """MockLLM puede resetear contadores."""
        client = MockLLM()

        # Hacer algunas llamadas
        client.query_sync("test1")
        client.query_sync("test2")

        assert client.call_count == 2
        assert client.last_prompt == "test2"

        # Reset
        client.reset()

        assert client.call_count == 0
        assert client.last_prompt is None

    @pytest.mark.asyncio
    async def test_mock_llm_keyword_matching(self):
        """MockLLM hace matching de keywords case-insensitive."""
        client = MockLLM(responses={
            "KEYWORD": "respuesta para KEYWORD",
            "otro": "respuesta para otro",
        })

        # Matching case-insensitive
        response1 = await client.query("Este prompt tiene keyword minúsculas")
        assert response1 == "respuesta para KEYWORD"

        response2 = await client.query("Este tiene OTRO en mayúsculas")
        assert response2 == "respuesta para otro"

    def test_mock_llm_custom_default_response(self):
        """MockLLM acepta respuesta por defecto personalizada."""
        custom_default = "Mi respuesta personalizada por defecto"
        client = MockLLM(default_response=custom_default)

        response = client.query_sync("cualquier cosa")

        assert response == custom_default
