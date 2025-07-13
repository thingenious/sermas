# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""PostgreSQL database manager for conversation and message storage."""
# pylint: disable=line-too-long
# flake8: noqa: E501
# pyright: reportUnknownArgumentType=false, reportUnknownVariableType=false

import json
import uuid
from typing import Any, Optional

from psycopg_pool import AsyncConnectionPool

from ._base import DatabaseManager


class PostgresDatabaseManager(DatabaseManager):
    """PostgreSQL database manager for conversation and message storage."""

    def __init__(self, database_url: str) -> None:
        """Initialize the database manager with the database URL.

        Parameters
        ----------
        database_url : str
            The database URL".
        """
        self.database_url = database_url
        self.pool: Optional[AsyncConnectionPool] = None

    async def init_db(self) -> None:
        """Initialize the database and create necessary tables."""
        self.pool = AsyncConnectionPool(self.database_url, open=False)
        await self.pool.open()
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                # EXTENSION for gen_random_uuid()
                await cur.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
                # conversations
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS conversations (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """
                )
                # messages
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        conversation_id UUID REFERENCES conversations(id),
                        role VARCHAR(10) NOT NULL,
                        content TEXT NOT NULL,
                        emotion VARCHAR(20) DEFAULT 'neutral',
                        sources JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """
                )
                # conversation_summaries
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS conversation_summaries (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        conversation_id UUID REFERENCES conversations(id),
                        summary TEXT NOT NULL,
                        message_count INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """
                )
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS admin_settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                    """
                )

    async def create_conversation(self) -> str:
        """Create a new conversation and return its ID.

        Returns
        -------
        str
            The ID of the newly created conversation.

        Raises
        ------
        RuntimeError
            If the database connection pool is not initialized.
        """
        if not self.pool:  # pragma: no cover
            raise RuntimeError("Database connection pool is not initialized.")
        conversation_id = str(uuid.uuid4())
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO conversations (id) VALUES (%s)",
                    (conversation_id,),
                )
        return conversation_id

    async def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        emotion: str = "neutral",
        sources: Optional[list[str]] = None,
    ) -> None:
        """Save a message in the conversation.

        Parameters
        ----------
        conversation_id : str
            The ID of the conversation to which the message belongs.
        role : str
            The role of the message sender (e.g., "user", "assistant").
        content : str
            The content of the message.
        emotion : str, optional
            The emotion associated with the message (default is "neutral").
        sources : Optional[list[str]], optional
            A list of sources associated with the message (default is None).

        Raises
        ------
        RuntimeError
            If the database connection pool is not initialized.
        """
        if not self.pool:  # pragma: no cover
            raise RuntimeError("Database connection pool is not initialized.")
        message_id = str(uuid.uuid4())
        sources_json = json.dumps(sources) if sources else None
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO messages (id, conversation_id, role, content, emotion, sources)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """,
                    (
                        message_id,
                        conversation_id,
                        role,
                        content,
                        emotion,
                        sources_json,
                    ),
                )

    async def get_conversation_messages(
        self, conversation_id: str, limit: int | None = 50
    ) -> list[dict[str, Any]]:
        """Retrieve messages from a conversation.

        Parameters
        ----------
        conversation_id : str
            The ID of the conversation to retrieve messages from.
        limit : int, optional
            The maximum number of messages to retrieve (default is 50).

        Returns
        -------
        list[dict[str, Any]]
            A list of messages in the conversation.

        Raises
        ------
        RuntimeError
            If the database connection pool is not initialized.
        """
        if not self.pool:  # pragma: no cover
            raise RuntimeError("Database connection pool is not initialized.")
        query = """
            SELECT role, content, emotion, sources, created_at
            FROM messages
            WHERE conversation_id = %s
            ORDER BY created_at DESC
            """
        args: tuple[Any, ...] = (conversation_id,)
        if limit is not None:
            query += " LIMIT %s"
            args = (conversation_id, limit)
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    query,
                    args,
                )
                rows = await cur.fetchall()
                # psycopg returns tuples; field order as specified
                return [
                    {
                        "role": row[0],
                        "content": row[1],
                        "emotion": row[2],
                        "sources": row[3] if row[3] else [],
                        "created_at": row[4].isoformat() if row[4] else None,
                    }
                    for row in reversed(rows)
                ]

    async def count_conversations(self) -> int:
        """Count the total number of conversations.

        Returns
        -------
        int
            The total number of conversations.

        Raises
        ------
        RuntimeError
            If the database connection pool is not initialized.
        """
        if not self.pool:  # pragma: no cover
            raise RuntimeError("Database connection pool is not initialized.")
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(*) FROM conversations")
                row = await cur.fetchone()
                return int(row[0]) if row else 0

    async def save_summary(
        self,
        conversation_id: str,
        summary: str,
        message_count: int,
    ) -> None:
        """Save a summary for a conversation.

        Parameters
        ----------
        conversation_id : str
            The ID of the conversation for which the summary is being saved.
        summary : str
            The summary text to be saved.
        message_count : int
            The number of messages in the conversation at the time of summary.

        Raises
        ------
        RuntimeError
            If the database connection pool is not initialized.
        """
        if not self.pool:  # pragma: no cover
            raise RuntimeError("Database connection pool is not initialized.")
        if not summary:  # pragma: no cover
            return
        summary_id = str(uuid.uuid4())
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO conversation_summaries (id, conversation_id, summary, message_count)
                    VALUES (%s, %s, %s, %s)
                """,
                    (summary_id, conversation_id, summary, message_count),
                )

    async def get_latest_summary(
        self, conversation_id: str
    ) -> Optional[dict[str, Any]]:
        """Retrieve the latest summary for a conversation.

        Parameters
        ----------
        conversation_id : str
            The ID of the conversation for which to retrieve the latest summary.

        Returns
        -------
        Optional[dict[str, Any]]
            A dictionary containing the latest summary, message count, and creation time,
            or None if no summary exists.

        Raises
        ------
        RuntimeError
            If the database connection pool is not initialized.
        """
        if not self.pool:  # pragma: no cover
            raise RuntimeError("Database connection pool is not initialized.")
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT summary, message_count, created_at
                    FROM conversation_summaries
                    WHERE conversation_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                    (conversation_id,),
                )
                row = await cur.fetchone()
                if row:
                    return {
                        "summary": row[0],
                        "message_count": row[1],
                        "created_at": row[2].isoformat() if row[2] else None,
                    }
                return None  # pragma: no cover

    async def get_admin_setting(self, key: str) -> Optional[str]:
        """Get an admin setting by key.

        Parameters
        ----------
        key : str
            The key of the admin setting to retrieve.

        Returns
        -------
        Optional[str]
            The value of the admin setting, or None if it does not exist.

        Raises
        ------
        RuntimeError
            If the database connection pool is not initialized.
        """
        if not self.pool:
            raise RuntimeError("Database connection pool is not initialized.")
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT value FROM admin_settings WHERE key = %s", (key,)
                )
                row = await cur.fetchone()
                return row[0] if row else None

    async def set_admin_setting(self, key: str, value: str) -> None:
        """Set an admin setting by key.

        Parameters
        ----------
        key : str
            The key of the admin setting to set.
        value : str
            The value to set for the admin setting.

        Raises
        ------
        RuntimeError
            If the database connection pool is not initialized.
        """
        if not self.pool:
            raise RuntimeError("Database connection pool is not initialized.")
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO admin_settings (key, value)
                    VALUES (%s, %s)
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                    """,
                    (key, value),
                )

    async def list_conversations(
        self, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """List conversations with pagination.

        Parameters
        ----------
        limit : int, optional
            The maximum number of conversations to return (default is 100).
        offset : int, optional
            The number of conversations to skip before
            starting to collect the result set (default is 0).

        Returns
        -------
        list[dict[str, Any]]
            A list of conversations,
            each represented as a dictionary with relevant metadata.

        Raises
        ------
        RuntimeError
            If the database connection pool is not initialized.
        """
        if not self.pool:
            raise RuntimeError("Database connection pool is not initialized.")
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, created_at, updated_at
                    FROM conversations
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """,
                    (limit, offset),
                )
                rows = await cur.fetchall()
                return [
                    {
                        "id": str(row[0]),
                        "created_at": row[1].isoformat(),
                        "updated_at": row[2].isoformat(),
                    }
                    for row in rows
                ]

    async def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation by its ID.

        Parameters
        ----------
        conversation_id : str
            The ID of the conversation to delete.

        Raises
        ------
        RuntimeError
            If the database connection pool is not initialized.
        """
        if not self.pool:
            raise RuntimeError("Database connection pool is not initialized.")
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM conversations WHERE id = %s",
                    (conversation_id,),
                )
                await cur.execute(
                    "DELETE FROM messages WHERE conversation_id = %s",
                    (conversation_id,),
                )
                await cur.execute(
                    "DELETE FROM conversation_summaries WHERE conversation_id = %s",
                    (conversation_id,),
                )

    async def close(self) -> None:
        """Close the database connection pool.

        Raises
        ------
        RuntimeError
            If the database connection pool is not initialized.
        """
        if self.pool:
            await self.pool.close()
            self.pool = None
        else:  # pragma: no cover
            raise RuntimeError("Database connection pool is not initialized.")
