# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""AioSqlite Database manager implementation."""
# pylint: disable=line-too-long
# flake8: noqa: E501
# pyright: reportUnknownArgumentType=false, reportUnknownVariableType=false

import json
import logging
import uuid
from typing import Any, Optional

import aiosqlite

from ._base import DatabaseManager


class AioSqliteDatabaseManager(DatabaseManager):
    """AioSqlite database manager for conversation and message storage."""

    def __init__(self, database_url: str):
        # Accepts sqlite:///chat.db or chat.db
        # remove any "+driver" .. in the url (this is for sqlalchemy
        if database_url.startswith("sqlite:///"):  # pragma: no cover
            self.db_path = database_url.replace("sqlite:///", "")
        else:
            self.db_path = database_url
        self.connection: Optional[aiosqlite.Connection] = None
        self.log = logging.getLogger(__name__)

    async def init_db(self) -> None:
        # Create tables once at startup; keep a persistent connection
        self.connection = await aiosqlite.connect(self.db_path)
        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                emotion TEXT DEFAULT 'neutral',
                sources TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        """
        )
        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_summaries (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                summary TEXT NOT NULL,
                message_count INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        """
        )
        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        await self.connection.commit()

    async def create_conversation(self) -> str:
        """Create a new conversation and return its ID.

        Returns
        -------
        str
            The ID of the newly created conversation.

        Raises
        ------
        RuntimeError
            If the database connection is not initialized.
        """
        if not self.connection:  # pragma: no cover
            raise RuntimeError("Database connection is not initialized.")
        conversation_id = str(uuid.uuid4())
        await self.connection.execute(
            "INSERT INTO conversations (id) VALUES (?)", (conversation_id,)
        )
        await self.connection.commit()
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
            If the database connection is not initialized.
        """
        if not self.connection:  # pragma: no cover
            raise RuntimeError("Database connection is not initialized.")
        message_id = str(uuid.uuid4())
        sources_json = json.dumps(sources) if sources else None
        await self.connection.execute(
            """
            INSERT INTO messages (id, conversation_id, role, content, emotion, sources)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (message_id, conversation_id, role, content, emotion, sources_json),
        )
        await self.connection.commit()

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
            If the database connection is not initialized.
        """
        if not self.connection:  # pragma: no cover
            raise RuntimeError("Database connection is not initialized.")
        query = """
            SELECT role, content, emotion, sources, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at DESC
        """
        args: tuple[Any, ...] = (conversation_id,)
        if limit is not None:
            query += " LIMIT ?"
            args = (conversation_id, limit)
        cursor = await self.connection.execute(query, args)
        rows = await cursor.fetchall()
        if not rows:  # pragma: no cover
            self.log.debug(
                "No messages found for conversation %s", conversation_id
            )
            return []
        return [
            {
                "role": row[0],
                "content": row[1],
                "emotion": row[2],
                "sources": json.loads(row[3]) if row[3] else [],
                "created_at": row[4],
            }
            for row in reversed(list(rows))
        ]

    async def save_summary(
        self, conversation_id: str, summary: str, message_count: int
    ) -> None:
        """Save a summary for a conversation.

        Parameters
        ----------
        conversation_id : str
            The ID of the conversation to which the summary belongs.
        summary : str
            The summary text for the conversation.
        message_count : int
            The number of messages in the conversation at the time of summarization.

        Raises
        ------
        RuntimeError
            If the database connection is not initialized.
        """
        if not self.connection:  # pragma: no cover
            raise RuntimeError("Database connection is not initialized.")
        summary_id = str(uuid.uuid4())
        await self.connection.execute(
            """
            INSERT INTO conversation_summaries (id, conversation_id, summary, message_count)
            VALUES (?, ?, ?, ?)
        """,
            (summary_id, conversation_id, summary, message_count),
        )
        await self.connection.commit()

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
            If the database connection is not initialized.
        """
        if not self.connection:  # pragma: no cover
            raise RuntimeError("Database connection is not initialized.")
        cursor = await self.connection.execute(
            """
            SELECT summary, message_count, created_at
            FROM conversation_summaries
            WHERE conversation_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """,
            (conversation_id,),
        )
        row = await cursor.fetchone()
        if row:
            return {
                "summary": row[0],
                "message_count": row[1],
                "created_at": row[2],
            }
        self.log.debug(  # pragma: no cover
            "No summary found for conversation %s", conversation_id
        )
        return None  # pragma: no cover

    async def count_conversations(self) -> int:
        """Count the total number of conversations.

        Returns
        -------
        int
            The total number of conversations.

        Raises
        ------
        RuntimeError
            If the database connection is not initialized.
        """
        if not self.connection:  # pragma: no cover
            raise RuntimeError("Database connection is not initialized.")
        cursor = await self.connection.execute(
            "SELECT COUNT(*) FROM conversations"
        )
        row = await cursor.fetchone()
        if row:
            return int(row[0])
        return 0  # pragma: no cover

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
            If the database connection is not initialized.
        """
        if not self.connection:
            raise RuntimeError("Database connection is not initialized.")
        cur = await self.connection.execute(
            "SELECT value FROM admin_settings WHERE key = ?", (key,)
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
            If the database connection is not initialized.
        """
        if not self.connection:
            raise RuntimeError("Database connection is not initialized.")
        await self.connection.execute(
            "INSERT OR REPLACE INTO admin_settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        await self.connection.commit()

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
            If the database connection is not initialized.
        """
        if not self.connection:
            raise RuntimeError("Database connection is not initialized.")
        # SQLite
        cur = await self.connection.execute(
            "SELECT id, created_at, updated_at FROM conversations ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = await cur.fetchall()
        return [
            {"id": row[0], "created_at": row[1], "updated_at": row[2]}
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
            If the database connection is not initialized.
        """
        if not self.connection:
            raise RuntimeError("Database connection is not initialized.")
        # Delete in order: messages, summaries, then conversation itself
        await self.connection.execute(
            "DELETE FROM messages WHERE conversation_id = ?", (conversation_id,)
        )
        await self.connection.execute(
            "DELETE FROM conversation_summaries WHERE conversation_id = ?",
            (conversation_id,),
        )
        await self.connection.execute(
            "DELETE FROM conversations WHERE id = ?", (conversation_id,)
        )
        await self.connection.commit()

    async def close(self) -> None:
        """Close the database connection.

        Raises
        ------
        RuntimeError
            If the database connection is not initialized.
        """
        if self.connection:
            await self.connection.close()
            self.connection = None
        else:  # pragma: no cover
            raise RuntimeError("Database connection is not initialized.")
