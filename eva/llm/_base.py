# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Base class for LLM managers."""

# pylint: disable=unused-argument,inconsistent-quotes
# pyright: reportReturnType=false
import logging
from typing import Any, AsyncIterator, Iterator, Protocol, runtime_checkable

from eva.models import ChatMessage, ValidEmotion

from .prompts import NEW_SUMMARY_PROMPT, UPDATE_SUMMARY_PROMPT
from .utils import (
    attempt_json_repair,
    clean_and_validate_json,
    fix_spacing_after_punctuation,
)


@runtime_checkable
class LLMManager(Protocol):
    """Protocol for a Language Model (LLM) manager."""

    async def initialize(self) -> None:
        """Initialize the LLM manager.

        This method is called during application startup to set up
        any necessary resources or configurations.
        """

    async def close(self) -> None:
        """Close the LLM manager.

        This method is called during application shutdown to clean up
        any resources or connections.
        """

    async def generate_response(
        self, messages: list[dict[str, Any]], rag_context: str = ""
    ) -> AsyncIterator[ChatMessage]:
        """Generate a response from the LLM.

        Based on the provided conversation history and optional RAG context,
        this method generates a response asynchronously.

        Parameters
        ----------
        messages : list[Dict]
            A list of message dictionaries containing the conversation history.
        rag_context : str, optional
            Context from the RAG system to be included
            in the response generation,
            by default an empty string.

        Yields
        ------
           ChatMessage
            An asynchronous generator yielding response messages.
        """

    async def summarize_conversation(
        self,
        messages: list[dict[str, Any]],
        previous_summary: str | None = None,
    ) -> str:
        """Summarize the conversation history.

        This method generates a summary of the conversation
        based on the provided messages.

        Parameters
        ----------
        messages : list[Dict]
            A list of message dictionaries containing the conversation history.
        previous_summary : str, optional
            An optional previous summary to include in the new summary,
            by default None.

        Returns
        -------
        str
            A summary of the conversation.
        """


class BaseLLMManager(LLMManager):
    """Base class for LLM managers."""

    def __init__(self, model_name: str, **kwargs: Any) -> None:
        """Initialize the LLM manager.

        Parameters
        ----------
        model_name : str
            The name of the LLM model to use.

        **kwargs : Any
            Additional keyword arguments for configuration.
        """
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize the LLM manager.

        This method is called during application startup to set up
        any necessary resources or configurations.
        """
        self.logger.info(
            "Initializing LLM manager for model: %s", self.model_name
        )

    async def close(self) -> None:
        """Close the LLM manager.

        This method is called during application shutdown to clean up
        any resources or connections.
        """
        self.logger.info("Closing LLM manager for model: %s", self.model_name)

    @staticmethod
    def get_summary_prompt(
        messages: list[dict[str, Any]],
        previous_summary: str | None = None,
    ) -> str:
        """Get the summary prompt based on the previous and new summaries.

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
            The formatted summary prompt.
        """
        conversation_text = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in messages]
        )
        if not previous_summary:
            summary_prompt = NEW_SUMMARY_PROMPT.format(
                conversation_text=conversation_text
            )
        else:
            summary_prompt = UPDATE_SUMMARY_PROMPT.format(
                conversation_text=conversation_text,
                previous_summary=previous_summary,
            )
        return summary_prompt

    def get_chat_message(self, response_text: str) -> Iterator[ChatMessage]:
        """Parse the response text into a ChatMessage object.

        Parameters
        ----------
        response_text : str
            The response text from the LLM.

        Yields
        ------
        ChatMessage
            An iterator yielding ChatMessage objects parsed from the response.
        """
        # pylint: disable=too-many-try-statements, broad-exception-caught
        self.logger.debug("Parsing response text: %s", response_text)
        try:
            # First attempt to repair common issues
            cleaned_response = attempt_json_repair(response_text)
            cleaned_response = fix_spacing_after_punctuation(cleaned_response)
            # Then validate and parse using your robust function
            response_data = clean_and_validate_json(cleaned_response)
            # response_data = json.loads(response_text)
            segments = response_data.get("segments", [])
            for i, segment in enumerate(segments):
                content = segment.get("content", "")
                emotion = self.validate_emotion(
                    segment.get("emotion", "neutral")
                )
                is_final = i == len(segments) - 1
                yield ChatMessage(
                    type="message",
                    content=content,
                    emotion=emotion,
                    is_final=is_final,
                )
        except ValueError as e:
            self.logger.error("Failed to validate JSON response: %s", e)
            self.logger.error("Raw response: %s", response_text)
            yield ChatMessage(
                type="message",
                content=response_text,
                emotion="neutral",
                is_final=True,
                metadata={
                    "error": str(e),
                    "raw_response": response_text,
                },
            )
        except BaseException as e:  # pragma: no cover
            self.logger.error("Unexpected error: %s", e)
            yield ChatMessage(
                type="error",
                content=f"Error processing response: {str(e)}",
                emotion="concerned",
                is_final=True,
            )

    @staticmethod
    def validate_emotion(emotion: str) -> str:
        """Validate and normalize the emotion string.

        Parameters
        ----------
        emotion : str
            The emotion string to validate and normalize.

        Returns
        -------
        str
            A normalized emotion string. If the input is not recognized,
            it defaults to "neutral".
        """
        mapping = {
            "sad": "concerned",
            "worried": "concerned",
            "enthusiastic": "excited",
            "analytical": "thoughtful",
            "questioning": "curious",
            "supportive": "empathetic",
            "caring": "empathetic",
            "positive": "happy",
            "negative": "concerned",
        }
        e = emotion.lower().strip()
        if e in ValidEmotion:
            return e
        return mapping.get(e, "neutral")
