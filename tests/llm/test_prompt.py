# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Tests for eva.llm.prompts.*."""

from eva.llm.prompts import BASE_SYSTEM_PROMPT


def test_prompt_content() -> None:
    """Test the content of the base system prompt."""
    assert (
        "Please structure your response as a JSON object" in BASE_SYSTEM_PROMPT
    )
    assert "segments" in BASE_SYSTEM_PROMPT
    assert "emotion" in BASE_SYSTEM_PROMPT
    assert "Your entire response must be valid JSON" in BASE_SYSTEM_PROMPT
