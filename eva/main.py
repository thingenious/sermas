# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Main entry point for the EVA application."""

# pyright: reportUnusedFunction=false
# pylint: disable=broad-exception-caught,too-many-try-statements,unused-argument
# pylint: disable=too-complex
import logging.config
import os
import sys
import traceback
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncIterator

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import ORJSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from eva._logging import get_logging_config
from eva.admin import router as admin_router
from eva.auth import extract_ws_token, verify_ws_token
from eva.config import settings
from eva.db import DatabaseManager, get_db_manager
from eva.llm import LLMManager, get_llm_manager
from eva.llm.prompts import BASE_SYSTEM_PROMPT
from eva.rag import RAGManager, get_rag_manager

from ._version import __version__


class EvaApp(FastAPI):
    """Custom FastAPI application class for EVA."""

    db_manager: DatabaseManager
    rag_manager: RAGManager
    llm_manager: LLMManager


@asynccontextmanager
async def lifespan(application: EvaApp) -> AsyncIterator[None]:
    """Application lifespan context manager.

    Parameters
    ----------
    application : EvaApp
        The FastAPI application

    Yields
    ------
    None
        Nothing
    """
    # On startup
    application.db_manager = get_db_manager()
    application.rag_manager = get_rag_manager()
    application.llm_manager = get_llm_manager()
    await application.db_manager.init_db()
    await application.rag_manager.initialize()
    await application.llm_manager.initialize()
    yield
    # On shutdown
    await application.db_manager.close()
    await application.llm_manager.close()


class ChatApplication:
    """Main application class for the EVA chat application."""

    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}
        self.log = logging.getLogger(__name__)
        self.app = EvaApp(
            lifespan=lifespan,
            docs_url="/docs",
            redoc_url=None,
            title="EVA",
            description="Simple chat application using FastAPI",
            version=__version__,
            openapi_url="/openapi.json",
            default_response_class=ORJSONResponse,
            license_info={
                "name": "Apache 2.0",
                "identifier": "Apache-2.0",
                "url": "https://www.apache.org/licenses/LICENSE-2.0",
            },
        )
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=(
                settings.trusted_origins if settings.trusted_origins else ["*"]
            ),
            allow_origin_regex=settings.trusted_origin_regex,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.app.add_middleware(
            ProxyHeadersMiddleware,  # type: ignore
            trusted_hosts=(
                settings.trusted_hosts if settings.trusted_hosts else ["*"]
            ),
        )
        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=(
                settings.trusted_hosts if settings.trusted_hosts else ["*"]
            ),
            www_redirect=False,
        )

        self.app.include_router(admin_router)

        @self.app.get("/health", include_in_schema=False)
        @self.app.get("/health/", include_in_schema=False)
        @self.app.get("/healthz", include_in_schema=False)
        @self.app.get("/healthz/", include_in_schema=False)
        async def health_check() -> ORJSONResponse:
            """Healthcheck endpoint.

            Returns
            -------
            ORJSONResponse
                The status.
            """
            return ORJSONResponse(content={"status": "ok"})

        @self.app.websocket("/ws")
        @self.app.websocket("/ws/")
        async def websocket_endpoint(websocket: WebSocket) -> None:
            """WebSocket endpoint for real-time communication.

            Parameters
            ----------
            websocket : WebSocket
                The WebSocket connection object.
            """
            token, subprotocol = extract_ws_token(websocket)
            if not token or not verify_ws_token(token):
                msg = (
                    "WebSocket connection attempt with invalid "
                    f"or missing API key: {token}"
                )
                self.log.warning(msg)
                await websocket.close(
                    code=1008, reason="Invalid or missing API key"
                )
                return
            await websocket.accept(subprotocol=subprotocol)
            connection_id = str(uuid.uuid4())
            self.active_connections[connection_id] = websocket
            try:
                await self.handle_websocket_connection(websocket, connection_id)
            except WebSocketDisconnect:
                self.log.info("WebSocket %s disconnected", connection_id)
            finally:
                if websocket in self.active_connections.values():
                    try:
                        await websocket.close()
                    except Exception as e:
                        self.log.debug(
                            "Error closing WebSocket %s: %s", connection_id, e
                        )
                self.active_connections.pop(connection_id, None)

    async def handle_websocket_connection(
        self,
        websocket: WebSocket,
        connection_id: str,
    ) -> None:
        """Handle WebSocket connection and message processing.

        Parameters
        ----------
        websocket : WebSocket
            The WebSocket connection object.
        connection_id : str
            Unique identifier for the WebSocket connection.
        """
        conversation_id: str | None = None
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_json()

                if data.get("type") == "start_conversation":
                    conversation_id = data.get("conversation_id")
                    if not conversation_id:
                        conversation_id = (
                            await self.app.db_manager.create_conversation()
                        )

                    # Send conversation started confirmation
                    await websocket.send_json(
                        {
                            "type": "conversation_started",
                            "conversation_id": conversation_id,
                        }
                    )

                elif data.get("type") == "user_message":
                    if not conversation_id:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "content": (
                                    "No active conversation. "
                                    "Please start a conversation first."
                                ),
                            }
                        )
                        continue

                    user_message = data.get("content", "")
                    await self.process_user_message(
                        websocket, conversation_id, user_message
                    )
        except WebSocketDisconnect:
            self.log.debug("WebSocket %s disconnected", connection_id)
        except Exception as e:
            self.log.debug("WebSocket error: %s", e)
            try:
                await websocket.send_json(
                    {"type": "error", "content": f"Server error: {str(e)}"}
                )
            except Exception as send_error:
                self.log.error(
                    "Error sending error message to client: %s", send_error
                )

    # pylint: disable=too-many-arguments,too-many-locals,
    # pylint: disable=too-complex,too-many-statements
    async def process_user_message(  # noqa: C901
        self, websocket: WebSocket, conversation_id: str, user_message: str
    ) -> None:
        """Process user message and generate response.

        Parameters
        ----------
        websocket : WebSocket
            The WebSocket connection object.
        conversation_id : str
            The ID of the conversation.
        user_message : str
            The content of the user message.

        Raises
        ------
        RuntimeError
            If there is an error during message processing
            or LLM response generation.
        """
        try:
            # Save user message
            await self.app.db_manager.save_message(
                conversation_id, "user", user_message
            )

            # Get conversation history
            messages = await self.app.db_manager.get_conversation_messages(
                conversation_id, settings.max_history_messages
            )
            self.log.debug(
                "Retrieved %d messages for conversation %s",
                len(messages),
                conversation_id,
            )

            # Check if we need to summarize old messages
            if len(messages) > settings.summary_threshold:
                await self.handle_conversation_summary(
                    conversation_id, messages
                )
                # Get updated messages after summarization
                # (keep recent messages + summary context)
                messages = await self.app.db_manager.get_conversation_messages(
                    conversation_id,
                    settings.max_history_messages
                    // 2,  # Keep fewer messages since we have summary
                )

                # Include latest summary as context for the LLM
                latest_summary = await self.app.db_manager.get_latest_summary(
                    conversation_id
                )
                if latest_summary:
                    # Prepend summary as a system context message
                    if "summary" in latest_summary and isinstance(
                        latest_summary["summary"], str
                    ):
                        latest_summary_str = latest_summary["summary"].strip()
                    else:
                        latest_summary_str = ""
                    if latest_summary_str:
                        summary_context = {
                            "role": "system",
                            "content": (
                                f"Previous conversation summary: "
                                f"{latest_summary_str}"
                            ),
                        }
                        messages.insert(0, summary_context)

            # Perform RAG search
            rag_results = await self.app.rag_manager.search(
                user_message, n_results=3
            )
            self.log.debug(
                "RAG search results for conversation %s: %s",
                conversation_id,
                rag_results,
            )
            rag_context = "\n".join([doc["content"] for doc in rag_results])
            prompt_in_db = await self.app.db_manager.get_admin_setting("prompt")
            if not prompt_in_db:
                prompt_in_db = BASE_SYSTEM_PROMPT
                await self.app.db_manager.set_admin_setting(
                    "prompt", prompt_in_db
                )
            system_prompt_parts = [prompt_in_db]

            # Summary (if available)
            latest_summary = await self.app.db_manager.get_latest_summary(
                conversation_id
            )
            summary = (latest_summary or {}).get("summary") or ""
            if isinstance(summary, str) and summary.strip():
                system_prompt_parts.append(
                    f"Previous conversation summary:\n{summary.strip()}"
                )

            # RAG context
            if rag_context.strip():
                system_prompt_parts.append(
                    f"Relevant context from documents:\n{rag_context.strip()}"
                )

            # Final system prompt
            full_system_prompt = "\n\n".join(system_prompt_parts)

            # Build full message list for LLM
            llm_messages: list[dict[str, Any]] = [
                {"role": "system", "content": full_system_prompt},
                *[
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in messages
                    if msg["role"]
                    != "system"  # Avoid accidental double system prompts
                ],
            ]

            # Generate and stream response
            response_chunks: list[str] = []
            sources = [doc["id"] for doc in rag_results] if rag_results else []

            try:
                async for chunk in await self.app.llm_manager.generate_response(
                    llm_messages, rag_context
                ):
                    chunk_data = chunk.model_dump(mode="json")
                    chunk_data["metadata"] = {
                        "conversation_id": conversation_id,
                        "timestamp": datetime.now(tz=timezone.utc)
                        .isoformat(timespec="milliseconds")
                        .replace("+00:00", "Z"),
                        "sources": sources,
                    }
                    try:
                        await websocket.send_json(chunk_data)
                        response_chunks.append(chunk.content)
                    except (WebSocketDisconnect, Exception):
                        # Client disconnected during streaming - exit gracefully
                        self.log.debug(
                            "Client disconnected during response streaming"
                        )
                        return
            except Exception as stream_error:
                self.log.error(
                    "Error during response streaming: %s", stream_error
                )
                raise RuntimeError(
                    "Error generating response from LLM"
                ) from stream_error
            if response_chunks:
                # Save complete response
                complete_response = " ".join(response_chunks)
                await self.app.db_manager.save_message(
                    conversation_id,
                    "assistant",
                    complete_response,
                    sources=sources,
                )

        except Exception as e:
            self.log.error("Error processing message: %s", e)
            try:
                await websocket.send_json(
                    {
                        "type": "error",
                        "content": f"Error processing your message: {str(e)}",
                        "emotion": "concerned",
                    }
                )
            except Exception as send_error:
                traceback.print_exc()
                self.log.error(
                    "Error sending error message to client: %s", send_error
                )

    async def handle_conversation_summary(
        self, conversation_id: str, messages: list[dict[str, Any]]
    ) -> None:
        """Handle conversation summarization when history gets too long.

        Parameters
        ----------
        conversation_id : str
            The ID of the conversation to summarize.
        messages : list[dict[str, Any]]
            The list of messages in the conversation.
        """
        try:
            # Get the latest existing summary
            previous_summary_data = (
                await self.app.db_manager.get_latest_summary(conversation_id)
            )
            previous_summary: str | None = ""
            if (
                previous_summary_data
                and "summary" in previous_summary_data
                and isinstance(previous_summary_data["summary"], str)
            ):
                previous_summary = previous_summary_data["summary"]

            # Determine which messages to summarize
            if previous_summary_data:
                # We have a previous summary,
                # so only summarize messages after the last summary
                messages_since_summary = (
                    len(messages) - previous_summary_data["message_count"]
                )
                messages_to_summarize = messages[
                    -messages_since_summary : -settings.summary_threshold // 4
                ]
            else:
                # No previous summary, summarize the oldest messages
                messages_to_summarize = messages[
                    : settings.summary_threshold // 2
                ]

            if not messages_to_summarize:
                self.log.info(
                    "No messages to summarize for conversation %s",
                    conversation_id,
                )
                return

            # Generate cumulative summary
            new_summary = await self.app.llm_manager.summarize_conversation(
                messages_to_summarize, previous_summary
            )

            # Calculate total message count covered by this summary
            total_message_count = len(messages_to_summarize)
            if previous_summary_data:
                total_message_count += previous_summary_data["message_count"]

            # Save the new summary
            await self.app.db_manager.save_summary(
                conversation_id, new_summary, total_message_count
            )

            self.log.info(
                "Updated cumulative summary for conversation %s (%d messages)",
                conversation_id,
                total_message_count,
            )

        except Exception as e:
            self.log.error("Error creating summary: %s", e)


def create_app() -> EvaApp:
    """Create and configure the FastAPI application.

    Returns
    -------
    FastAPI
        The configured FastAPI application instance.
    """
    chat_app = ChatApplication()
    return chat_app.app


if "--log-level" in sys.argv:
    log_level_index = sys.argv.index("--log-level") + 1
    if log_level_index < len(sys.argv):
        os.environ["LOG_LEVEL"] = sys.argv[log_level_index]
        settings.log_level = sys.argv[log_level_index]

logging_config = get_logging_config(settings.log_level.upper())
logging.config.dictConfig(logging_config)

app = create_app()


if __name__ == "__main__":
    logging.info("Starting EVA application version %s", __version__)
    uvicorn.run(
        "eva.main:app",
        host=settings.eva_host,
        port=settings.eva_port,
        log_level=settings.log_level,
        proxy_headers=True,
        ws_ping_timeout=None,
        server_header=False,
        date_header=False,
        forwarded_allow_ips="*",
        # ws="wsproto", // it seems that it won't work with subprotocol auth
    )
    logging.info("EVA application started successfully")
