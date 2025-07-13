# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Unit tests for Anthropic LLM Manager."""

# pylint: disable=missing-return-doc,missing-param-doc,missing-yield-doc
# pylint: disable=missing-function-docstring,missing-class-docstring
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eva.llm._anthropic import AnthropicLLMManager
from eva.models import ChatMessage


@pytest.mark.asyncio
@patch("eva.llm._anthropic.AsyncAnthropic")
async def test_anthropic_manager_parses_json(mock_anthropic: AsyncMock) -> None:
    """Test that the Anthropic LLM manager correctly parses JSON responses."""
    # Simulate Anthropic client
    mock_resp = AsyncMock()
    mock_resp.messages.create.return_value.content = [
        type(
            "Obj",
            (),
            {"text": '{"segments": [{"content": "Hi!", "emotion": "happy"}]}'},
        )()
    ]
    mock_anthropic.return_value = mock_resp

    manager = AnthropicLLMManager()
    messages = [{"role": "user", "content": "hi"}]
    chunks: list[ChatMessage] = []
    async for chunk in await manager.generate_response(messages):
        chunks.append(chunk)
    assert chunks[0].content == "Hi!"
    assert chunks[0].emotion == "happy"


@pytest.mark.asyncio
@patch("eva.llm._anthropic.AsyncAnthropic")
async def test_anthropic_generate_response_error(
    mock_anthropic: AsyncMock,
) -> None:
    """Test that Anthropic LLM manager handles errors gracefully."""
    mock_client = AsyncMock()
    mock_client.messages.create.side_effect = Exception("boom")
    mock_anthropic.return_value = mock_client

    manager = AnthropicLLMManager()
    messages = [{"role": "user", "content": "test"}]
    gen = await manager.generate_response(messages)
    chunks = [chunk async for chunk in gen]
    assert any("Error generating response" in c.content for c in chunks)


@pytest.mark.asyncio
@patch("eva.llm._anthropic.AsyncAnthropic")
async def test_anthropic_summarize_conversation(
    mock_anthropic: AsyncMock,
) -> None:
    """Test that Anthropic LLM manager summarizes conversation correctly."""
    mock_response = MagicMock()
    mock_response.content = [{"text": "Anthropic summary!"}]
    mock_client = AsyncMock()
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    manager = AnthropicLLMManager()
    messages = [{"role": "user", "content": "Hi"}]
    result = await manager.summarize_conversation(messages)
    assert result == "Anthropic summary!"


@pytest.mark.asyncio
@patch("eva.llm._anthropic.AsyncAnthropic")
async def test_anthropic_summarize_conversation_error(
    mock_anthropic: AsyncMock,
) -> None:
    """Test that Anthropic LLM manager handles errors in summarization."""
    mock_client = AsyncMock()
    mock_client.messages.create.side_effect = Exception("fail!")
    mock_anthropic.return_value = mock_client

    manager = AnthropicLLMManager()
    messages = [{"role": "user", "content": "Hi"}]
    result = await manager.summarize_conversation(messages)
    assert result == "Conversation summary unavailable"
    await manager.close()
