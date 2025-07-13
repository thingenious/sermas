# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Tests for eva.db.postgres.*."""
# pylint: disable=missing-return-doc,missing-param-doc,missing-yield-doc
# pylint: disable=missing-function-docstring,missing-class-docstring

from typing import AsyncGenerator, Generator

import pytest
from testcontainers.postgres import (  # type: ignore[import-untyped]
    PostgresContainer,
)

from eva.db._postgres import PostgresDatabaseManager
from tests.conftest import is_docker_available

pytestmark = pytest.mark.skipif(
    not is_docker_available(),
    reason="Docker not available, skipping Postgres integration tests.",
)


@pytest.fixture(scope="module", name="postgres_url")
def postgres_url_fixture() -> Generator[str, None, None]:
    """Spins up a temporary Postgres container for the test module."""
    with PostgresContainer("postgres:17") as postgres:
        # testcontainers returns a psycopg2 URL, but psycopg3 works with it too
        db_url = postgres.get_connection_url()
        db_url = db_url.replace("+psycopg2", "").replace("+psycopg", "")
        yield db_url


@pytest.fixture(name="db_manager")
async def db_manager_fixture(
    postgres_url: str,
) -> AsyncGenerator[PostgresDatabaseManager, None]:
    """Fixture to create an instance of PostgresDatabaseManager."""
    db = PostgresDatabaseManager(postgres_url)
    await db.init_db()
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_create_and_retrieve_conversation(
    db_manager: PostgresDatabaseManager,
) -> None:
    """Test creating and retrieving a conversation."""
    conversation_id = await db_manager.create_conversation()
    assert isinstance(conversation_id, str)
    await db_manager.save_message(conversation_id, "user", "Hello!", "curious")
    msgs = await db_manager.get_conversation_messages(conversation_id)
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "Hello!"
    assert msgs[0]["emotion"] == "curious"


@pytest.mark.asyncio
async def test_summary_crud(db_manager: PostgresDatabaseManager) -> None:
    """Test creating, retrieving, and updating conversation summaries."""
    conversation_id = await db_manager.create_conversation()
    await db_manager.save_summary(conversation_id, "The sum", 9)
    summary = await db_manager.get_latest_summary(conversation_id)
    assert summary is not None
    assert summary["summary"] == "The sum"
    assert summary["message_count"] == 9
