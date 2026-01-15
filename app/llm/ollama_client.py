"""
LLM Client - Implementación unificada para Ollama y Mock
Soporta modo mock (sin GPU) y Ollama real (con GPU)
"""

import logging
from typing import Optional

import httpx

from app.core.config import get_settings
from app.llm.interface import LLMClient

logger = logging.getLogger(__name__)


class OllamaClient(LLMClient):
    """
    Cliente unificado para LLM (SOLID: Single Responsibility)
    
    Modos de operación:
    - Mock: Respuestas educativas predefinidas (sin GPU)
    - Ollama: LLM real local (requiere GPU y Ollama instalado)
    """

    # Respuestas mock categorizadas por contexto
    MOCK_RESPONSES = {
        "treatment": (
            "**Explicación del Estado Actual:**\n\n"
            "El tumor ha alcanzado un volumen que requiere intervención "
            "terapéutica. Las células cancerosas siguen un crecimiento "
            "gompertziano, donde la tasa de crecimiento disminuye a medida "
            "que el tumor se acerca a la capacidad de carga del tejido pulmonar.\n\n"
            "**Recomendación Educativa:**\n\n"
            "En casos similares según NCCN Guidelines 2024:\n"
            "- **Estadio I-II**: Resección quirúrgica + quimioterapia adyuvante\n"
            "- **Estadio III**: Quimiorradioterapia + inmunoterapia (durvalumab)\n"
            "- **Estadio IV**: Inmunoterapia o terapia dirigida según mutaciones\n\n"
            "**Disclaimer:** Simulación educativa. Las decisiones clínicas reales "
            "requieren evaluación completa por oncólogo."
        ),
        "progression": (
            "**Análisis de Progresión Tumoral:**\n\n"
            "El modelo matemático (Gompertz modificado) muestra crecimiento "
            "exponencial temprano. Tiempo de duplicación: ~120-180 días, "
            "consistente con adenocarcinomas pulmonares.\n\n"
            "**Mecanismo Biológico:**\n"
            "- Células sensibles dominan el volumen\n"
            "- Angiogénesis activa para volúmenes >0.5 cm³\n"
            "- Posible desarrollo de hipoxia central\n\n"
            "**Interpretación Educativa:**\n"
            "Patrón típico de NSCLC sin tratamiento. Intervención temprana "
            "(estadios I-II) tiene supervivencia a 5 años del 60-80%.\n\n"
            "**Fuente:** SEER Database 2015-2020, NCCN Guidelines v3.2024"
        ),
        "default": (
            "**Análisis General del Caso:**\n\n"
            "La simulación refleja un caso de NSCLC con parámetros realistas. "
            "El modelo considera:\n\n"
            "1. **Factores de Riesgo:** Edad, tabaquismo, dieta\n"
            "2. **Dinámica Tumoral:** Crecimiento gompertziano bifásico\n"
            "3. **Respuesta a Tratamiento:** Eficacia según tipo y resistencia\n\n"
            "**Objetivo Educativo:**\n"
            "Comprender cómo los factores del paciente influyen en la progresión. "
            "Las decisiones clínicas requieren evidencia y análisis molecular.\n\n"
            "**Nota:** Este simulador tiene fines educativos únicamente."
        ),
    }

    # Cliente HTTP compartido para connection pooling
    _shared_client: Optional[httpx.AsyncClient] = None
    
    def __init__(self, force_mock: bool = False):
        """
        Args:
            force_mock: Si True, usa mock aunque Ollama esté disponible (para tests)
        """
        self.settings = get_settings()
        self._force_mock = force_mock
        self._ollama_available: Optional[bool] = None

    @classmethod
    def get_http_client(cls) -> httpx.AsyncClient:
        """Cliente HTTP singleton con connection pooling (optimización)"""
        if cls._shared_client is None:
            cls._shared_client = httpx.AsyncClient(
                timeout=httpx.Timeout(15.0, connect=5.0),  # 15s max, 5s connect
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
        return cls._shared_client
    
    @classmethod
    async def close_client(cls) -> None:
        """Cerrar cliente HTTP (llamar en shutdown)"""
        if cls._shared_client is not None:
            await cls._shared_client.aclose()
            cls._shared_client = None

    @property
    def is_available(self) -> bool:
        """Verifica si Ollama está disponible (lazy check síncrono)"""
        if self._force_mock:
            return False
        
        if self._ollama_available is None:
            self._ollama_available = self._check_ollama_connection_sync()
        
        return self._ollama_available

    def _check_ollama_connection_sync(self) -> bool:
        """Verifica conexión con Ollama server (síncrono para startup)"""
        try:
            # Usamos httpx síncrono solo para el check inicial
            with httpx.Client(timeout=2.0) as client:
                response = client.get(f"{self.settings.ollama_base_url}/api/tags")
                if response.status_code == 200:
                    logger.info(f"✅ Ollama disponible en {self.settings.ollama_base_url}")
                    return True
        except Exception as e:
            logger.debug(f"Ollama no disponible: {e}")
        
        return False

    async def query(self, prompt: str) -> str:
        """
        Envía prompt al LLM y retorna respuesta (ASYNC).
        Usa mock si Ollama no está disponible o timeout.
        
        Optimizado para VR:
        - Timeout de 15 segundos máximo
        - Fallback automático a mock
        - Connection pooling para múltiples requests
        """
        if not self.is_available:
            return self._mock_response(prompt)

        return await self._ollama_query_async(prompt)

    async def _ollama_query_async(self, prompt: str) -> str:
        """Consulta async a Ollama con timeout agresivo"""
        try:
            client = self.get_http_client()
            
            response = await client.post(
                f"{self.settings.ollama_base_url}/api/generate",
                json={
                    "model": self.settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.settings.ollama_temperature,
                        "num_predict": self.settings.ollama_max_tokens,
                    }
                },
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            
            logger.warning(f"Ollama HTTP {response.status_code}, usando mock")
            return self._mock_response(prompt)
            
        except httpx.TimeoutException:
            logger.warning("⏱️ Ollama timeout (>15s), usando respuesta mock")
            return self._mock_response(prompt)
        except Exception as e:
            logger.error(f"Error Ollama: {e}")
            return self._mock_response(prompt)
    
    def query_sync(self, prompt: str) -> str:
        """Versión síncrona para compatibilidad con tests"""
        if not self.is_available:
            return self._mock_response(prompt)
        
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(
                    f"{self.settings.ollama_base_url}/api/generate",
                    json={
                        "model": self.settings.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": self.settings.ollama_temperature,
                            "num_predict": self.settings.ollama_max_tokens,
                        }
                    },
                )
                if response.status_code == 200:
                    return response.json().get("response", "")
        except Exception as e:
            logger.error(f"Error Ollama sync: {e}")
        
        return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        """Genera respuesta mock educativa basada en el contexto del prompt"""
        prompt_lower = prompt.lower()
        
        if "tratamiento" in prompt_lower or "treatment" in prompt_lower:
            return self.MOCK_RESPONSES["treatment"]
        
        if any(kw in prompt_lower for kw in ["progresión", "volumen", "progression"]):
            return self.MOCK_RESPONSES["progression"]
        
        return self.MOCK_RESPONSES["default"]

    def check_availability(self) -> bool:
        """Implementación del protocolo LLMClient"""
        return self.is_available

    def get_model_name(self) -> str:
        """Retorna el nombre del modelo en uso"""
        if self.is_available:
            return f"ollama-{self.settings.ollama_model}"
        return "ollama-mock"
