"""Application configuration using pydantic-settings."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Keys
    serper_api_key: str = ""
    groq_api_key: str = ""

    # Mock providers (for testing without API keys)
    use_mock_serp: bool = False
    use_mock_llm: bool = False

    # LLM Settings
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 8000

    # Article defaults
    default_word_count: int = 1500
    default_language: str = "en"

    # Paths
    data_dir: Path = Path("data")
    jobs_dir: Path = Path("data/jobs")

    # SEO validation thresholds
    min_word_count_tolerance: float = 0.9  # 90% of target
    max_word_count_tolerance: float = 1.1  # 110% of target
    min_h2_count: int = 4
    min_h3_count: int = 2
    meta_description_min_length: int = 120
    meta_description_max_length: int = 160
    max_keyword_density: float = 0.03  # 3%

    @property
    def has_serper_key(self) -> bool:
        return bool(self.serper_api_key)

    @property
    def has_groq_key(self) -> bool:
        return bool(self.groq_api_key)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
