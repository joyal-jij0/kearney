"""Configuration module for environment variables."""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenRouter Configuration
    openrouter_api_key: str = Field(
        ...,
        alias="OPENROUTER_API_KEY",
        description="OpenRouter API key"
    )

    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL",
        description="Base URL for OpenRouter API"
    )

    model_name: str = Field(
        default="openai/gpt-4o-mini",
        alias="MODEL_NAME",
        description="Model to use for AI queries"
    )

    app_name: str = Field(
        default="DataAnalysisAPI",
        alias="APP_NAME",
        description="Application name for OpenRouter"
    )

    # Database Configuration
    database_path: str = Field(
        default="data/uploads.db",
        alias="DATABASE_PATH",
        description="Path to SQLite database file"
    )

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance.
    
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
