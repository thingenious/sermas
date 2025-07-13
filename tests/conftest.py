# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Setup for pytest configuration to check Docker availability."""

# pylint: disable=missing-function-docstring,missing-param-doc,missing-yield-doc
# pylint: disable=unused-argument,too-few-public-methods
import os
import shutil
import subprocess
from pathlib import Path

import pytest


def is_docker_available() -> bool:
    """Check if Docker is available/running, else False.

    Returns
    -------
    bool
        True if Docker is available and running, False otherwise.
    """
    try:
        subprocess.run(  # nosemgrep # nosec
            ["docker", "info"],
            capture_output=True,
            check=True,
        )
        return True
    except Exception:  # pylint: disable=broad-exception-caught
        return False


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest to skip tests requiring Docker if not available.

    Parameters
    ----------
    config : pytest.Config
        The pytest configuration object.
    """
    # Register custom marker for clarity (optional)
    config.addinivalue_line("markers", "docker: mark test as requiring Docker")
    worker_id = getattr(config, "workerinput", {}).get("workerid", "master")

    project_dir = Path(__file__).resolve().parent.parent

    if worker_id == "master":
        # Single process mode
        _setup_single_process_env(project_dir)
    else:
        # Multi-worker mode - each worker gets its own .env
        _setup_worker_env(project_dir, worker_id)


def _setup_single_process_env(project_dir: Path) -> None:
    """Single process testing."""
    env_file = project_dir / ".env"
    backup_file = project_dir / ".env.pytest_backup"

    # Backup original
    if env_file.exists():
        shutil.copy(env_file, backup_file)

    # Create test .env
    _create_test_env_file(env_file)


def _setup_worker_env(project_dir: Path, worker_id: str) -> None:
    """Multi-worker testing."""
    # Each worker gets its own .env file
    worker_env_file = project_dir / f".env.{worker_id}"
    # original_env_file = project_dir / ".env"

    # Create worker-specific test .env
    _create_test_env_file(worker_env_file)

    # Update pydantic settings to use worker-specific file
    os.environ["PYDANTIC_ENV_FILE"] = str(worker_env_file)


def _create_test_env_file(env_file: Path) -> None:
    """Create a test .env file."""
    with open(env_file, "w", encoding="utf-8") as f:
        f.write("CHAT_API_KEY=super-secret\n")
        f.write("DATABASE_URL=sqlite:///test.db\n")
        f.write("LOG_LEVEL=info\n")


def pytest_unconfigure(config: pytest.Config) -> None:
    """Clean up after all tests."""
    worker_id = getattr(config, "workerinput", {}).get("workerid", "master")
    project_dir = Path(__file__).resolve().parent.parent

    if worker_id == "master":
        _cleanup_single_process(project_dir)
    else:
        _cleanup_worker(project_dir, worker_id)


def _cleanup_single_process(project_dir: Path) -> None:
    """Cleanup for single process."""
    env_file = project_dir / ".env"
    backup_file = project_dir / ".env.pytest_backup"

    if backup_file.exists():
        if env_file.exists():
            env_file.unlink()
        shutil.move(backup_file, env_file)
    else:
        # No backup means no original .env
        if env_file.exists():
            env_file.unlink()


def _cleanup_worker(project_dir: Path, worker_id: str) -> None:
    """Cleanup for worker process."""
    worker_env_file = project_dir / f".env.{worker_id}"
    if worker_env_file.exists():
        worker_env_file.unlink()
