"""
Groq LLM Client - Para pruebas locales sin GPU/Ollama
Usa la API de Groq (gratuita con límites) como alternativa a Ollama

Configuración:
    1. Obtener API key en: https://console.groq.com/keys
    2. Crear archivo .env con: GROQ_API_KEY=gsk_xxxxx
    3. En config.py: llm_provider = "groq"
"""
import logging
from typing import Optional
import httpx

from app.core.config import get_settings
from app.llm.interface import LLMClient

logger = logging.getLogger(__name__)


class GroqClient(LLMClient):
    """
    Cliente para Groq API (alternativa gratuita a OpenAI/Ollama)

    Modelos disponibles (gratuitos):
    - llama-3.3-70b-versatile: Mejor calidad, más lento
    - llama-3.1-8b-instant: Rápido, buena calidad
    - mixtral-8x7b-32768: Buen balance
    - gemma2-9b-it: Ligero y rápido
    """

    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

    # Cliente HTTP compartido para connection pooling
    _shared_client: Optional[httpx.AsyncClient] = None

    def __init__(self):
        self.settings = get_settings()
        self._api_key = self.settings.groq_api_key
        self._model = self.settings.groq_model

    @classmethod
    def get_http_client(cls) -> httpx.AsyncClient:
        """Cliente HTTP singleton con connection pooling"""
        if cls._shared_client is None:
            cls._shared_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
        return cls._shared_client

    @classmethod
    async def close_client(cls) -> None:
        """Cerrar cliente HTTP (llamar en shutdown)"""
        if cls._shared_client is not None:
            await cls._shared_client.aclose()
            cls._shared_client = None

    def check_availability(self) -> bool:
        """Verifica si Groq está configurado"""
        return bool(self._api_key and self._api_key.startswith("gsk_"))

    async def query(self, prompt: str) -> str:
        """
        Envía prompt a Groq y retorna respuesta

        Args:
            prompt: El prompt completo (sistema + contexto + pregunta)

        Returns:
            Respuesta del modelo
        """
        if not self.check_availability():
            logger.warning("⚠️ Groq API key no configurada, usando fallback")
            return self._fallback_response()

        client = self.get_http_client()

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Eres un profesor de medicina especializado en oncología pulmonar. "
                        "Respondes en español con información educativa precisa. "
                        "Siempre citas fuentes como NCCN Guidelines o SEER Database."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.settings.groq_temperature,
            "max_tokens": self.settings.groq_max_tokens,
        }

        try:
            response = await client.post(
                self.GROQ_API_URL,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            logger.info(f"✅ Groq respondió ({self._model}): {len(content)} chars")
            return content

        except httpx.TimeoutException:
            logger.error("⏱️ Timeout en Groq API")
            return self._fallback_response()

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Error HTTP Groq: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 429:
                return "⚠️ Límite de rate alcanzado en Groq. Espera unos segundos."
            return self._fallback_response()

        except Exception as e:
            logger.error(f"❌ Error inesperado Groq: {e}")
            return self._fallback_response()

    def _fallback_response(self) -> str:
        """Respuesta de fallback cuando Groq no está disponible"""
        return (
            "**Análisis del Caso:**\n\n"
            "El sistema de IA está en modo de prueba. "
            "El estado actual del tumor requiere evaluación según las guías NCCN.\n\n"
            "**Recomendación Educativa:**\n"
            "Para casos de NSCLC, consultar:\n"
            "- NCCN Guidelines v3.2024\n"
            "- SEER Database para estadísticas de supervivencia\n\n"
            "**Nota:** Esta es una respuesta de fallback. "
            "Configure GROQ_API_KEY para respuestas personalizadas."
        )


# Factory function para obtener cliente según configuración
def get_llm_client() -> LLMClient:
    """
    Factory: Retorna cliente LLM según configuración

    Prioridad:
    1. Groq (si GROQ_API_KEY está configurada)
    2. Ollama (si está disponible localmente)
    3. Mock (fallback siempre disponible)
    """
    settings = get_settings()

    # Si hay API key de Groq, usarla
    if settings.groq_api_key and settings.groq_api_key.startswith("gsk_"):
        logger.info("🚀 Usando Groq como LLM provider")
        return GroqClient()

    # Fallback a Ollama
    from app.llm.ollama_client import OllamaClient
    logger.info("🔄 Groq no configurado, usando Ollama/Mock")
    return OllamaClient()
