from abc import ABC, abstractmethod
from typing import Any


class ModelProvider(ABC):
    name: str = "base"
    is_demonstration: bool = False

    @abstractmethod
    async def is_available(self) -> bool:
        ...

    @abstractmethod
    async def generate_response(
        self,
        system: str,
        user: str,
        context: str | None = None,
    ) -> str:
        ...

    @abstractmethod
    async def summarize_artifact(self, filename: str, content: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def extract_entities(self, content: str, artifact_id: str) -> list[dict]:
        ...

    @abstractmethod
    async def identify_connections(
        self, artifacts: list[dict], clues: list[dict]
    ) -> list[dict]:
        ...

    async def retrieve_relevant_context(
        self, query: str, artifacts: list[dict], top_k: int = 5
    ) -> list[dict]:
        from app.retrieval import keyword_retrieve

        return keyword_retrieve(query, artifacts, top_k)

    @abstractmethod
    async def reconstruct_timeline(
        self, artifacts: list[dict], events: list[dict]
    ) -> list[dict]:
        ...

    @abstractmethod
    async def generate_final_report(
        self,
        investigation: dict,
        artifacts: list[dict],
        clues: list[dict],
        timeline: list[dict],
    ) -> dict[str, Any]:
        ...

    def list_models(self) -> list[dict]:
        return []
