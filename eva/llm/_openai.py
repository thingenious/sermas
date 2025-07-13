# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""OpenAI LLM manager implementation."""

# pylint: disable=too-many-try-statements,broad-exception-caught,too-complex
import asyncio
from typing import Any, AsyncIterator

import openai
from openai.types.responses import ResponseInputParam

from eva.config import settings
from eva.models import ChatMessage

from ._base import BaseLLMManager


class OpenAILLMManager(BaseLLMManager):
    """OpenAI LLM manager implementation."""

    def __init__(self, model_name: str = "gpt-4.1") -> None:
        """Initialize the OpenAI LLM manager.

        Parameters
        ----------
        model_name : str, optional
            The name of the OpenAI model to use,
            by default "gpt-4.1".
        """
        super().__init__(model_name=model_name)
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    async def close(self) -> None:
        """Close the OpenAI client connection."""
        if self.client:  # pragma: no branch
            try:
                await self.client.close()
            except Exception as e:  # pragma: no cover
                self.logger.error("Error closing OpenAI client: %s", e)

    async def generate_response(
        self, messages: list[dict[str, Any]], rag_context: str = ""
    ) -> AsyncIterator[ChatMessage]:
        """Generate a response from the OpenAI LLM.

        Parameters
        ----------
        messages : list[dict[str, Any]]
            A list of message dictionaries containing the conversation history.
        rag_context : str, optional
            Context from the RAG system to be included
            in the response generation, by default an empty string.

        Returns
        -------
        AsyncGenerator[Any, None]
            An asynchronous generator yielding response messages.
        """

        async def _response_generator() -> AsyncIterator[ChatMessage]:
            formatted_messages: ResponseInputParam = []
            for message in messages:
                role = message.get("role", "user").lower()
                content = message.get("content", "")
                if role not in {
                    "user",
                    "assistant",
                    "system",
                }:  # pragma: no cover
                    self.logger.warning(
                        "OpenAI: Invalid '%s' in message, defaulting to 'user'",
                        role,
                    )
                    role = "user"
                formatted_messages.append({"role": role, "content": content})
            try:
                response = await self.client.responses.create(
                    model=self.model_name,
                    input=formatted_messages,
                )
                response_text = response.output_text.strip()
                for entry in self.get_chat_message(response_text):
                    yield entry
                    if not entry.is_final:  # pragma: no cover
                        try:
                            await asyncio.sleep(0.3)
                        except asyncio.CancelledError:
                            break
            except GeneratorExit:
                return
            except Exception as e:  # pragma: no cover
                self.logger.error("OpenAI API error: %s", e)
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
        """Summarize the conversation history.

        Parameters
        ----------
        messages : list[dict[str, Any]]
            A list of message dictionaries containing the conversation history.

        previous_summary : str, optional
            An optional previous summary to include in the new summary,
            by default None.

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
            response = await self.client.responses.create(
                model=self.model_name,
                input=[{"role": "user", "content": summary_prompt}],
            )
            return response.output_text.strip()
        except Exception as e:  # pragma: no cover
            self.logger.error("OpenAI summary error: %s", e)
            return "Conversation summary unavailable"
