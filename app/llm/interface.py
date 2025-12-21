from typing import Protocol


class LLMClient(Protocol):
    """Protocol for LLM clients used by the app.

    Synchronous interface with a deterministic `query` method used in tests.
    """

    def query(self, prompt: str) -> str:
        ...

    def check_availability(self) -> bool:
        ...
