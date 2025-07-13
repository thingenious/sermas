# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Anthropic LLM manager for generating responses and summaries."""

# pylint: disable=too-many-try-statements,broad-exception-caught
import asyncio
import logging
from typing import Any, AsyncIterator

from anthropic import AsyncAnthropic
from anthropic.types import Message, MessageParam

from eva.config import settings
from eva.models import ChatMessage

from ._base import BaseLLMManager
from .prompts import BASE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AnthropicLLMManager(BaseLLMManager):
    """Anthropic LLM manager implementation."""

    def __init__(
        self,
        model_name: str = "claude-3-5-sonnet-20241022",
        max_tokens: int | None = None,
    ) -> None:
        """Initialize the Anthropic LLM manager.

        Parameters
        ----------
        model_name : str, optional
            The name of the Anthropic model to use,
            by default "claude-3-5-sonnet-20241022".
        """
        super().__init__(model_name=model_name)
        self.max_tokens = max_tokens or settings.llm_max_tokens
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def close(self) -> None:
        if self.client:  # pragma: no branch
            try:
                await self.client.close()
            except Exception as e:  # pragma: no cover
                logger.error("Error closing Anthropic client: %s", e)

    async def generate_response(
        self,
        messages: list[dict[str, Any]],
        rag_context: str | None = None,
    ) -> AsyncIterator[ChatMessage]:
        """Generate a response from the Anthropic LLM.

        Parameters
        ----------
        messages : list[dict[str, Any]]
            A list of message dictionaries containing the conversation history.

        rag_context : str, optional
            Context from the RAG system to be included
            in the response generation, by default None.

        Returns
        -------
        AsyncIterator[ChatMessage]
            An asynchronous generator yielding response messages.
        """

        async def _response_generator() -> AsyncIterator[ChatMessage]:
            """Generate and yield response messages."""
            system_prompt = BASE_SYSTEM_PROMPT
            if rag_context:  # pragma: no cover
                system_prompt += (
                    f"\n\nRelevant context from documents:\n{rag_context}"
                )

            formatted_messages: list[MessageParam] = [
                {
                    "role": "user" if msg["role"] == "user" else "assistant",
                    "content": msg["content"],
                }
                for msg in messages
            ]
            try:
                response = await self.client.messages.create(
                    model=self.model_name,
                    max_tokens=self.max_tokens,
                    system=system_prompt,
                    messages=formatted_messages,
                )
                response_text = self.get_response_text(response)
                for entry in self.get_chat_message(response_text):
                    yield entry
                    if not entry.is_final:  # pragma: no cover
                        await asyncio.sleep(0.3)
            except Exception as e:  # pragma: no cover
                logger.error("Anthropic API error: %s", e)
                yield ChatMessage(
                    type="error",
                    content=f"Error generating response: {str(e)}",
                    emotion="concerned",
                    is_final=True,
                )

        return _response_generator()

    async def summarize_conversation(
        self,
        messages: list[dict[str, Any]],
        previous_summary: str | None = None,
    ) -> str:
        """Summarize the conversation history using Anthropic LLM.

        Parameters
        ----------
        messages : list[dict[str, Any]]
            A list of message dictionaries containing the conversation history.
        previous_summary : str, optional
            An optional previous summary to include in the new summary,

        Returns
        -------
        str
            A summary of the conversation.
        """
        summary_prompt = self.get_summary_prompt(
            messages=messages,
            previous_summary=previous_summary,
        )
        try:
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=150,
                messages=[{"role": "user", "content": summary_prompt}],
            )
            return self.get_response_text(response)
        except Exception as e:  # pragma: no cover
            logger.error("Anthropic summary error: %s", e)
            return "Conversation summary unavailable"

    @staticmethod
    def get_response_text(response: Message) -> str:
        """Extract text content from an Anthropic message response.

        Parameters
        ----------
        response : Message
            The Anthropic message response object.

        Returns
        -------
        str
            The text content of the message.
        """
        if not response or not hasattr(response, "content"):  # pragma: no cover
            return ""
        response_content = getattr(response, "content", [])
        if not response_content or not isinstance(
            response_content, list
        ):  # pragma: no cover
            return ""
        content = response_content[0]  # pyright: ignore
        if isinstance(content, str):  # pragma: no cover
            return content.strip()
        if (
            isinstance(content, dict)
            and "text" in content
            and isinstance(content["text"], str)
        ):
            return content["text"].strip()
        content_text = getattr(content, "text", None)  # pyright: ignore
        if isinstance(content_text, str):  # pragma: no cover
            return content_text.strip()
        return ""  # pragma: no cover
