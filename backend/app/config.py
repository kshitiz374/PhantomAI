from pathlib import Path
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_prefix="PHANTOM_", env_file=".env")

    data_dir: Path = Path(__file__).resolve().parent.parent / "data"
    db_filename: str = "phantom.db"
    max_artifact_bytes: int = 2 * 1024 * 1024  # 2 MB
    allowed_extensions: frozenset[str] = frozenset(
        {".txt", ".md", ".markdown", ".json", ".csv", ".log"}
    )
    ollama_base_url: str = "http://127.0.0.1:11434"
    default_chat_model: str = "qwen2.5:3b"
    default_embed_model: str = "nomic-embed-text"
    model_provider: str = "mock"  # mock | ollama
    semantic_search_enabled: bool = False
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @property
    def db_path(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir / self.db_filename


settings = Settings()
