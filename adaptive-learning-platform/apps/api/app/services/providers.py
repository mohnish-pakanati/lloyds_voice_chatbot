from abc import ABC, abstractmethod
from pydantic import BaseModel
from ..schemas import StructuredTeacherOutput


class LLMProvider(ABC):
    @abstractmethod
    def structured(self, *, instructions: str, prompt: str, schema: type[BaseModel]) -> BaseModel: ...


class FakeLLMProvider(LLMProvider):
    def structured(self, *, instructions: str, prompt: str, schema: type[BaseModel]) -> BaseModel:
        if schema is StructuredTeacherOutput:
            return schema.model_validate({
                "mode": "SOCRATIC",
                "message": "What constraint most directly makes full fine-tuning infeasible here?",
                "next_action": "attempt",
                "citations": [],
            })
        raise ValueError(f"No deterministic fixture for {schema.__name__}")


class OpenAILLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def structured(self, *, instructions: str, prompt: str, schema: type[BaseModel]) -> BaseModel:
        response = self.client.responses.parse(
            model=self.model,
            instructions=instructions,
            input=prompt,
            text_format=schema,
            store=False,
        )
        if response.output_parsed is None:
            raise ValueError("Provider returned no validated structured output")
        return response.output_parsed


class ResearchProvider(ABC):
    @abstractmethod
    def search(self, query: str) -> list[dict]: ...


class CuratedResearchProvider(ResearchProvider):
    def search(self, query: str) -> list[dict]:
        manifest = __import__("app.services.compiler", fromlist=["demo_manifest"]).demo_manifest()
        return [source.model_dump(mode="json") for source in manifest.sources]


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...
