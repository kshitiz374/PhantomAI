from app.providers.base import ModelProvider
from app.providers.mock_provider import MockProvider
from app.providers.ollama_provider import OllamaProvider
from app.config import settings

_provider: ModelProvider | None = None


def get_provider() -> ModelProvider:
    global _provider
    if _provider is None:
        _provider = _build_provider(settings.model_provider)
    return _provider


def set_provider(name: str, **kwargs) -> ModelProvider:
    global _provider
    if name == "ollama":
        base = kwargs.get("ollama_base_url") or settings.ollama_base_url
        chat = kwargs.get("chat_model") or settings.default_chat_model
        embed = kwargs.get("embed_model") or settings.default_embed_model
        _provider = OllamaProvider(base_url=base, chat_model=chat, embed_model=embed)
    else:
        _provider = MockProvider()
    settings.model_provider = name
    return _provider


def _build_provider(name: str) -> ModelProvider:
    if name == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            chat_model=settings.default_chat_model,
            embed_model=settings.default_embed_model,
        )
    return MockProvider()
