from typing import Dict

from .interface import LLMClient


class MockLLM(LLMClient):
    """Deterministic mock LLM for tests.

    Returns canned responses based on keywords and always includes a
    short explanation placeholder. Useful to assert grounding and sources.
    """

    def __init__(self, deterministic_responses: Dict[str, str] | None = None):
        # mapping of keyword -> response
        self.responses = deterministic_responses or {}
        self.available = True

    def query(self, prompt: str) -> str:
        lower = prompt.lower()
        for key, resp in self.responses.items():
            if key in lower:
                return resp

        # default deterministic response that echoes instruction to cite sources
        return (
            "RESPUESTA_MOCK: Basado únicamente en las fuentes provistas. "
            "Explicación breve. [CITAS: ver 'fuentes' en la respuesta estructurada]"
        )

    def check_availability(self) -> bool:
        return self.available
