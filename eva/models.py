# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Models for Eva's chat system."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from typing_extensions import Literal

Emotion = Literal[
    "neutral",
    "happy",
    "excited",
    "thoughtful",
    "curious",
    "confident",
    "concerned",
    "empathetic",
]
"""Possible emotion labels for chat messages."""

ValidEmotion = {
    "neutral",
    "happy",
    "excited",
    "thoughtful",
    "curious",
    "confident",
    "concerned",
    "empathetic",
}


class ChatMessage(BaseModel):
    """Represents a single message in the chat conversation."""

    type: str = Field(
        ..., description="Type of message: 'message', 'system', or 'error'"
    )
    content: str = Field(..., description="Content of the message")
    emotion: str = Field(
        "neutral", description="Emotion label for this segment"
    )
    chunk_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique chunk ID"
    )
    is_final: bool = Field(
        False, description="True if this is the last chunk/segment"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extra metadata (conversation_id, timestamp, sources, etc)",
    )


class ConversationSummary(BaseModel):
    """Represents a summary of a conversation."""

    conversation_id: str
    summary: str
    message_count: int
    created_at: datetime


class ConversationStartRequest(BaseModel):
    """Request to start a new conversation or continue an existing one."""

    conversation_id: Optional[str] = (
        None  # If client wants to continue, else None
    )


class ConversationStartedResponse(BaseModel):
    """Response when a conversation is started or continued."""

    type: str = "conversation_started"
    conversation_id: str


class UserMessageRequest(BaseModel):
    """Request containing a user message to be processed."""

    type: str = "user_message"
    content: str


class ErrorResponse(BaseModel):
    """Response for errors encountered during processing."""

    type: str = "error"
    content: str
    emotion: str = "concerned"


# If you need a model for LLM-segmented responses:
class LLMResponseSegment(BaseModel):
    """Represents a segment of the response from an LLM."""

    content: str
    emotion: str


class LLMResponse(BaseModel):
    """Represents a complete response from an LLM, segmented."""

    segments: List[LLMResponseSegment]
