# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Test cases for AioSqliteDatabaseManager."""

# pylint: disable=missing-return-doc,missing-param-doc,missing-yield-doc
# pylint: disable=missing-function-docstring,missing-class-docstring
from pathlib import Path
from typing import AsyncGenerator

import pytest

from eva.db._aiosqlite import AioSqliteDatabaseManager


@pytest.fixture(name="db_file")
async def db_file_fixture(tmp_path: Path) -> AsyncGenerator[str, None]:
    """Fixture to create a temporary SQLite database file."""
    # Use a temp file for DB
    db_path = tmp_path / "test_chat.db"
    yield str(db_path)
    # Cleanup is automatic for tmp_path


@pytest.fixture(name="db_manager")
async def db_manager_fixture(
    db_file: str,
) -> AsyncGenerator[AioSqliteDatabaseManager, None]:
    """Fixture to create an instance of AioSqliteDatabaseManager."""
    db = AioSqliteDatabaseManager(db_file)
    await db.init_db()
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_create_and_retrieve_conversation(
    db_manager: AioSqliteDatabaseManager,
) -> None:
    """Test creating and retrieving a conversation."""
    conversation_id = await db_manager.create_conversation()
    assert isinstance(conversation_id, str)
    # Insert and retrieve messages
    await db_manager.save_message(conversation_id, "user", "Hello!", "happy")
    msgs = await db_manager.get_conversation_messages(conversation_id)
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "Hello!"
    assert msgs[0]["emotion"] == "happy"


@pytest.mark.asyncio
async def test_summary_crud(db_manager: AioSqliteDatabaseManager) -> None:
    """Test creating, retrieving, and updating conversation summaries."""
    conversation_id = await db_manager.create_conversation()
    await db_manager.save_summary(conversation_id, "A summary", 5)
    summary = await db_manager.get_latest_summary(conversation_id)
    assert summary is not None
    assert summary["summary"] == "A summary"
    assert summary["message_count"] == 5
