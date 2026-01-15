from typing import Protocol, Union
from typing_extensions import runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for LLM clients used by the app.

    Soporta tanto interface sync como async para flexibilidad:
    - Async: Usado en producción para no bloquear event loop
    - Sync: Usado en tests para simplicidad
    """

    async def query(self, prompt: str) -> str:
        """Envía prompt al LLM y retorna respuesta (async)."""
        ...

    def check_availability(self) -> bool:
        """Verifica si el LLM está disponible."""
        ...
