# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Configuration settings for the EVA application using Pydantic."""

# pylint: disable=unused-argument
import os
from typing import Any

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for the EVA application."""

    # General app config
    chat_api_key: str = "super-secret"
    admin_api_key: str = "super-secret-admin"
    database_url: str = "sqlite:///chat.db"
    llm_provider: str = "openai"  # "anthropic"  # or "openai"

    # LLM-specific
    llm_max_tokens: int = 4096
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Conversation and summarization
    max_history_messages: int = 50
    summary_threshold: int = 30

    # RAG
    rag_docs_folder: str = "documents"

    # ChromaDB
    chroma_local: bool = True
    chroma_collection_name: str = "eve_rag"
    chroma_host: str = "localhost"
    chroma_port: int = 8888
    chroma_db_dir: str = "chroma_db"

    # FastAPI
    eva_host: str = "0.0.0.0"
    eva_port: int = 8000
    trusted_origins: str | list[str] = "*"
    trusted_origin_regex: str | None = None
    trusted_hosts: str | list[str] = "*"
    skip_admin: bool = False

    # Logging
    log_level: str = "info"

    @field_validator("trusted_hosts", "trusted_origins", mode="before")
    @classmethod
    def split_str_value(cls, value: Any, info: ValidationInfo) -> list[str]:
        """Split the value if it is a string.

        Parameters
        ----------
        value : Any
            The value
        info : ValidationInfo
            The validation info

        Returns
        -------
        List[str]
            The value as a list
        """
        if isinstance(value, str):
            if value.count(",") >= 1:  # pragma: no cover
                return [item for item in value.split(",") if item]

            return [value] if value else []
        if isinstance(value, list):  # pragma: no cover
            return [item for item in value if item]  # pyright: ignore
        return []  # pragma: no cover

    model_config = SettingsConfigDict(
        env_prefix="",  # No prefix: env vars are e.g. "DATABASE_URL"
        env_file=os.environ.get("PYDANTIC_ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields not defined in the model
    )


settings = Settings()
