# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Test main application functionality with WebSocket support."""
# pylint: disable=missing-return-doc,missing-param-doc,missing-yield-doc
# pylint: disable=missing-function-docstring,unused-argument

import asyncio
import os
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from httpx_ws import aconnect_ws
from httpx_ws._exceptions import WebSocketDisconnect
from httpx_ws.transport import ASGIWebSocketTransport

from eva.main import create_app
from eva.models import ChatMessage


@pytest.mark.asyncio
async def test_websocket_with_query() -> None:
    """Test that the WebSocket connection works as expected."""
    api_key = os.getenv("CHAT_API_KEY", "super-secret")
    app = create_app()
    with patch("eva.main.settings.chat_api_key", api_key):
        async with httpx.AsyncClient(
            transport=ASGIWebSocketTransport(app)
        ) as client:
            async with aconnect_ws(
                f"http://server/ws?token={api_key}",
                client,
            ):
                pass
            with pytest.raises(WebSocketDisconnect):
                async with aconnect_ws(
                    "http://server/ws?token=invalid_token",
                    client,
                ):
                    pass


@pytest.mark.asyncio
async def test_websocket_with_subprotocol() -> None:
    """Test that the WebSocket connection works with subprotocols."""
    api_key = os.getenv("CHAT_API_KEY", "super-secret")
    app = create_app()
    with patch("eva.main.settings.chat_api_key", api_key):
        async with httpx.AsyncClient(
            transport=ASGIWebSocketTransport(app)
        ) as client:
            async with aconnect_ws(
                "http://server/ws",
                client,
                subprotocols=["token", api_key],
            ):
                pass
            with pytest.raises(WebSocketDisconnect):
                async with aconnect_ws(
                    "http://server/ws",
                    client,
                    subprotocols=["token", "invalid_token"],
                ):
                    pass


@pytest.mark.asyncio
async def test_websocket_chat_with_managers_mocked() -> None:
    """Test the WebSocket chat functionality with mocked managers."""
    # -- create app instance
    app = create_app()

    # -- Create Mocks (LLM, RAG, DB)
    # Mock for llm_manager.generate_response
    async def fake_llm_response(
        *args: Any, **kwargs: Any
    ) -> AsyncGenerator[ChatMessage, None]:
        """Fake LLM response for testing."""

        async def generate() -> AsyncGenerator[ChatMessage, None]:
            """Messages generator."""
            yield ChatMessage(
                type="message",
                content="Paris is the capital of France.",
                emotion="confident",
                metadata={"sources": ["source1"]},
                is_final=True,
            )
            # Simulate a delay for streaming response
            await asyncio.sleep(0.1)

        return generate()

    mock_llm = MagicMock()
    mock_llm.generate_response = fake_llm_response
    mock_llm.summarize_conversation = AsyncMock(return_value="A summary.")
    mock_llm.initialize = AsyncMock()
    mock_llm.close = AsyncMock()

    # Mock for rag_manager.search
    mock_rag = MagicMock()
    mock_rag.search = AsyncMock(
        return_value=[
            {"content": "France is a country in Europe.", "id": "source1"},
        ]
    )
    mock_rag.initialize = AsyncMock()

    # Mock for db_manager (minimal, just conversation CRUD)
    mock_db = MagicMock()
    mock_db.create_conversation = AsyncMock(return_value="conv123")
    mock_db.save_message = AsyncMock()
    mock_db.get_conversation_messages = AsyncMock(
        return_value=[
            {"role": "user", "content": "What's the capital of France?"},
        ]
    )
    mock_db.get_latest_summary = AsyncMock(return_value=None)
    mock_db.save_summary = AsyncMock()
    mock_db.init_db = AsyncMock()
    mock_db.close = AsyncMock()

    # Patch them in the EvaApp instance
    app.llm_manager = mock_llm
    app.rag_manager = mock_rag
    app.db_manager = mock_db

    # --- run the websocket test ---
    api_key = "super-secret"
    with patch("eva.main.settings.chat_api_key", api_key):
        async with httpx.AsyncClient(
            transport=ASGIWebSocketTransport(app)
        ) as client:
            async with aconnect_ws(  # type: ignore
                f"http://server/ws?token={api_key}",
                client,
            ) as ws:
                # Start conversation
                await ws.send_json({"type": "start_conversation"})
                started = await ws.receive_json()
                assert started["type"] == "conversation_started"
                conv_id = started["conversation_id"]
                assert conv_id == "conv123"

                # User sends message
                await ws.send_json(
                    {
                        "type": "user_message",
                        "conversation_id": conv_id,
                        "content": "What's the capital of France?",
                    }
                )

                # Assistant responds
                response = await ws.receive_json()
                assert response["type"] == "message"
                assert response["content"] == "Paris is the capital of France."
                assert response["emotion"] == "confident"
                assert response["metadata"]["sources"] == ["source1"]
                assert response["is_final"] is True


@pytest.mark.asyncio
async def test_websocket_chat_handles_llm_error() -> None:
    """Test WebSocket chat functionality when LLM raises an error."""
    app = create_app()

    # Setup as before, but this time cause
    # llm_manager.generate_response to raise
    async def raise_error(
        *args: Any, **kwargs: Any
    ) -> AsyncGenerator[ChatMessage, None]:
        raise RuntimeError("LLM broke")

    mock_llm = MagicMock()
    mock_llm.generate_response = raise_error
    mock_llm.summarize_conversation = AsyncMock(return_value="A summary.")
    mock_llm.initialize = AsyncMock()
    mock_llm.close = AsyncMock()

    # Keep the other mocks as before
    mock_rag = MagicMock()
    mock_rag.search = AsyncMock(
        return_value=[{"content": "irrelevant", "id": "src"}]
    )
    mock_rag.initialize = AsyncMock()
    mock_db = MagicMock()
    mock_db.create_conversation = AsyncMock(return_value="conv123")
    mock_db.save_message = AsyncMock()
    mock_db.get_conversation_messages = AsyncMock(
        return_value=[
            {"role": "user", "content": "What's the capital of France?"},
        ]
    )
    mock_db.get_latest_summary = AsyncMock(return_value=None)
    mock_db.save_summary = AsyncMock()
    mock_db.init_db = AsyncMock()
    mock_db.close = AsyncMock()
    app.llm_manager = mock_llm
    app.rag_manager = mock_rag
    app.db_manager = mock_db

    api_key = "super-secret"
    with patch("eva.main.settings.chat_api_key", api_key):
        async with httpx.AsyncClient(
            transport=ASGIWebSocketTransport(app)
        ) as client:
            async with aconnect_ws(  # type: ignore
                f"http://server/ws?token={api_key}",
                client,
            ) as ws:
                await ws.send_json({"type": "start_conversation"})
                started = await ws.receive_json()
                assert started["type"] == "conversation_started"
                conv_id = started["conversation_id"]
                # Now, send a user message that will trigger LLM error
                await ws.send_json(
                    {
                        "type": "user_message",
                        "conversation_id": conv_id,
                        "content": "break please",
                    }
                )
                # Should receive an error message from the server
                resp = await ws.receive_json()
                assert resp["type"] == "error"
                assert (
                    "LLM broke" in resp["content"]
                    or "Error processing your message" in resp["content"]
                )
