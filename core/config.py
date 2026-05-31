# lean-data-kit/core/config.py
"""
Configuration module for the Lean Data Starter Kit.
Loads environment variables using Pydantic Settings with full validation.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    """
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    DUCKDB_PATH: str = "data.duckdb"

    # Pydantic v2 settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instantiate the global settings object
try:
    settings = Settings()
except Exception as e:
    # Fallback to defaults if parsing fails
    print(f"Error loading configuration, using default settings: {e}")
    settings = Settings(_env_file=None)
