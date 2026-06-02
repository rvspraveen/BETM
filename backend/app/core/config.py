"""
Central configuration — all settings pulled from environment variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "ERCOT Copilot API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # ── Database ─────────────────────────────────────────────────────────────
    POSTGRES_USER: str = "copilot"
    POSTGRES_PASSWORD: str = "copilot_secret"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ercot_copilot"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ── Redis ────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── LLM ──────────────────────────────────────────────────────────────────
    # Set LLM_PROVIDER=anthropic to switch to Claude
    LLM_PROVIDER: Literal["openai", "anthropic"] = "openai"
    OPENAI_API_KEY: str = "sk-placeholder"
    OPENAI_MODEL: str = "gpt-4o"
    ANTHROPIC_API_KEY: str = "sk-ant-placeholder"
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # Embeddings always use OpenAI (best-in-class for this use case)
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536

    # ── LangGraph ────────────────────────────────────────────────────────────
    MAX_RETRIEVAL_CHUNKS: int = 8
    CONFIDENCE_THRESHOLD: float = 0.72   # below this → route to human review
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.1             # low temp for grounded answers

    # ── Ingestion ────────────────────────────────────────────────────────────
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    DATA_DIR: str = "/app/data"


settings = Settings()
