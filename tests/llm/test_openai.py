# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Test for OpenAI LLM Manager JSON Parsing."""

# pylint: disable=missing-return-doc,missing-param-doc,missing-yield-doc
# pylint: disable=missing-function-docstring,missing-class-docstring
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eva.llm._openai import OpenAILLMManager
from eva.models import ChatMessage


@pytest.mark.asyncio
@patch("eva.llm._openai.openai")
async def test_openai_manager_parses_json(mock_openai: AsyncMock) -> None:
    """Test that the OpenAI LLM manager correctly parses JSON responses."""
    # Build a mock response object with output_text as the LLM's JSON string
    mock_response = MagicMock()
    mock_response.output_text = """
    {
        "segments": [
            {"content": "Hi!", "emotion": "curious"}
        ]
    }
    """

    # Patch the client's async responses.create method
    #  to return the mock_response
    mock_client = AsyncMock()
    mock_client.responses.create.return_value = mock_response
    mock_openai.AsyncOpenAI.return_value = mock_client

    manager = OpenAILLMManager()
    messages = [{"role": "user", "content": "test"}]
    chunks: list[ChatMessage] = []
    async for chunk in await manager.generate_response(messages):
        chunks.append(chunk)
    assert chunks[0].content == "Hi!"
    assert chunks[0].emotion == "curious"


@pytest.mark.asyncio
@patch("eva.llm._openai.openai")
async def test_openai_generate_response_error(mock_openai: AsyncMock) -> None:
    """Test that OpenAI LLM manager handles errors gracefully."""
    mock_client = AsyncMock()
    mock_client.responses.create.side_effect = Exception("boom")
    mock_openai.AsyncOpenAI.return_value = mock_client

    manager = OpenAILLMManager()
    messages = [{"role": "user", "content": "test"}]
    gen = await manager.generate_response(messages)
    chunks = [chunk async for chunk in gen]
    assert any("Error generating response" in c.content for c in chunks)


@pytest.mark.asyncio
@patch("eva.llm._openai.openai")
async def test_openai_summarize_conversation(mock_openai: AsyncMock) -> None:
    """Test that OpenAI LLM manager summarizes conversation correctly."""
    # Simulate OpenAI returning a summary string
    mock_response = MagicMock()
    mock_response.output_text = "This is the summary."
    mock_client = AsyncMock()
    mock_client.responses.create.return_value = mock_response
    mock_openai.AsyncOpenAI.return_value = mock_client

    manager = OpenAILLMManager()
    messages = [{"role": "user", "content": "Hello"}]
    result = await manager.summarize_conversation(messages)
    assert result == "This is the summary."


@pytest.mark.asyncio
@patch("eva.llm._openai.openai")
async def test_openai_summarize_conversation_error(
    mock_openai: AsyncMock,
) -> None:
    """Test that OpenAI LLM manager handles errors in summarization."""
    mock_client = AsyncMock()
    mock_client.responses.create.side_effect = Exception("fail!")
    mock_openai.AsyncOpenAI.return_value = mock_client

    manager = OpenAILLMManager()
    messages = [{"role": "user", "content": "Hello"}]
    result = await manager.summarize_conversation(messages)
    assert result == "Conversation summary unavailable"
    await manager.close()
