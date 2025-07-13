# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Database module for the application."""

from eva.config import settings

from ._aiosqlite import AioSqliteDatabaseManager
from ._base import DatabaseManager
from ._postgres import PostgresDatabaseManager


def get_db_manager() -> DatabaseManager:
    """Get the appropriate database manager based on the database URL.

    Returns
    -------
    DatabaseManager
        An instance of the database manager for the configured database.
    """
    url = settings.database_url
    if "sqlite" in url:
        return AioSqliteDatabaseManager(url)
    return PostgresDatabaseManager(url)  # pragma: no cover


__all__ = [
    "DatabaseManager",
    "get_db_manager",
]
