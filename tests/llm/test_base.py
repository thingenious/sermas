# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Tests for BaseLLMManager functionality."""
# pylint: disable=missing-return-doc,missing-param-doc,missing-yield-doc
# pylint: disable=missing-function-docstring,missing-class-docstring

import pytest

from eva.llm._base import BaseLLMManager
from eva.models import LLMResponse


def test_get_summary_prompt_new_and_update() -> None:
    """Test getting summary prompt with and without previous summary."""
    msgs = [{"role": "user", "content": "Hello!"}]
    out1 = BaseLLMManager.get_summary_prompt(msgs)
    assert "Hello!" in out1
    # With previous summary
    out2 = BaseLLMManager.get_summary_prompt(msgs, "This is a prev sum.")
    assert "This is a prev sum." in out2


def test_get_chat_message_valid_json() -> None:
    """Test parsing a valid JSON response from LLM."""
    resp = (
        '{"segments":[{"content":"Hi!","emotion":"happy"},'
        '{"content":"Bye.","emotion":"neutral"}]}'
    )
    manager = BaseLLMManager(model_name="dummy")  # type: ignore[abstract]
    segments = list(manager.get_chat_message(resp))
    assert segments[0].content == "Hi!"
    assert segments[0].emotion == "happy"
    assert segments[-1].is_final is True


def test_get_chat_message_invalid_json() -> None:
    """Test handling of invalid JSON response from LLM."""
    bad_resp = "NOT JSON AT ALL"
    manager = BaseLLMManager(model_name="dummy")  # type: ignore[abstract]
    segments = list(manager.get_chat_message(bad_resp))
    assert len(segments) == 1
    assert segments[0].type == "message"
    assert segments[0].emotion == "neutral"


def test_validate_emotion() -> None:
    """Test emotion validation and normalization."""
    assert BaseLLMManager.validate_emotion("excited") == "excited"
    assert BaseLLMManager.validate_emotion("sad") == "concerned"
    assert BaseLLMManager.validate_emotion("POSITIVE") == "happy"
    assert BaseLLMManager.validate_emotion("unknownzzz") == "neutral"


def test_parse_llm_response_valid() -> None:
    """Test parsing a valid JSON response from LLM."""
    # Simulated output from LLM
    response_text = """
    {
        "segments": [
            {"content": "Hello!", "emotion": "happy"},
            {"content": "How can I help?", "emotion": "neutral"}
        ]
    }
    """
    parsed = LLMResponse.model_validate_json(response_text)
    assert len(parsed.segments) == 2
    assert parsed.segments[0].content == "Hello!"
    assert parsed.segments[0].emotion == "happy"


@pytest.mark.asyncio
async def test_manager_lifecycle() -> None:
    """Test the lifecycle methods of BaseLLMManager."""
    mgr = BaseLLMManager(model_name="test-model")  # type: ignore[abstract]
    await mgr.initialize()
    await mgr.close()
