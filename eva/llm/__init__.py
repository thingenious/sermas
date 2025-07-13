# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""LLM Manager package initializer."""

from eva.config import settings

from ._anthropic import AnthropicLLMManager
from ._base import LLMManager
from ._openai import OpenAILLMManager


def get_llm_manager() -> LLMManager:
    """Get the appropriate LLM manager based on the configured provider.

    Returns
    -------
    LLMManager
        An instance of the appropriate LLM manager.

    Raises
    ------
    ValueError
        If the configured LLM provider is not supported.
    """
    if settings.llm_provider.lower() == "anthropic":
        return AnthropicLLMManager()
    if settings.llm_provider.lower() == "openai":
        return OpenAILLMManager()
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


__all__ = [
    "LLMManager",
    "get_llm_manager",
]
