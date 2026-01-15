"""
Mock LLM para tests unitarios
Permite inyectar respuestas determinísticas para pruebas
"""

from typing import Dict, Optional

from app.llm.interface import LLMClient


class MockLLM(LLMClient):
    """
    Mock LLM determinístico para tests.
    Permite configurar respuestas específicas por keywords.
    """

    # Respuesta por defecto cuando no hay match
    DEFAULT_RESPONSE = (
        "RESPUESTA_MOCK: Basado en las fuentes provistas. "
        "Explicación educativa del caso clínico."
    )

    def __init__(
        self,
        responses: Optional[Dict[str, str]] = None,
        default_response: Optional[str] = None,
    ):
        """
        Args:
            responses: Dict de keyword -> respuesta (busca keyword en prompt)
            default_response: Respuesta cuando no hay match con keywords
        """
        self.responses = responses or {}
        self.default_response = default_response or self.DEFAULT_RESPONSE
        self._available = True
        self.call_count = 0
        self.last_prompt: Optional[str] = None

    def query(self, prompt: str) -> str:
        """Retorna respuesta determinística basada en keywords"""
        self.call_count += 1
        self.last_prompt = prompt
        
        prompt_lower = prompt.lower()
        
        for keyword, response in self.responses.items():
            if keyword.lower() in prompt_lower:
                return response
        
        return self.default_response

    def check_availability(self) -> bool:
        """Siempre disponible en tests"""
        return self._available

    def set_available(self, available: bool) -> None:
        """Permite simular que el LLM no está disponible"""
        self._available = available

    def reset(self) -> None:
        """Resetea contadores para tests"""
        self.call_count = 0
        self.last_prompt = None
