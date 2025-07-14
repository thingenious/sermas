# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.
"""Test eva.admin.*."""

# mypy: disable-error-code="method-assign"
# pyright: reportArgumentType=false
# pylint: disable=missing-return-doc,missing-param-doc,missing-yield-doc
# pylint: disable=missing-function-docstring,missing-class-docstring
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from eva.config import settings
from eva.main import EvaApp, create_app


@pytest.fixture(name="test_app")
def test_app_fixture() -> "EvaApp":
    """Create a test application instance."""
    app = create_app()
    app.db_manager = MagicMock()
    app.db_manager.get_admin_setting = AsyncMock(return_value="Prompt here")
    app.db_manager.set_admin_setting = AsyncMock()
    app.db_manager.list_conversations = AsyncMock(return_value=["c1", "c2"])
    app.db_manager.count_conversations = AsyncMock(return_value=2)
    app.db_manager.get_conversation_messages = AsyncMock(
        return_value=[{"role": "user", "content": "hi"}]
    )
    app.db_manager.delete_conversation = AsyncMock()

    app.rag_manager = MagicMock()
    app.rag_manager.reload_documents = AsyncMock()
    return app


@pytest.fixture(name="test_client")
def test_client_fixture(test_app: "EvaApp") -> TestClient:
    """Create a test client for the application."""
    return TestClient(test_app)


@pytest.fixture(name="auth_header")
def auth_header_fixture() -> dict[str, str]:
    """Create an authorization header for admin access."""
    return {"Authorization": f"Bearer {settings.admin_api_key}"}


def test_unauthorized_admin_access(
    test_client: TestClient,
) -> None:
    """Test that admin endpoints require authorization."""
    response = test_client.get(
        "/admin/prompt", headers={"Authorization": "Invalid"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_authorized_admin_access(
    test_client: TestClient,
    auth_header: dict[str, str],
) -> None:
    """Test that admin endpoints require authorization."""
    response = test_client.get("/admin/prompt", headers=auth_header)
    assert response.status_code == status.HTTP_200_OK


def test_get_prompt(
    test_client: TestClient,
    test_app: "EvaApp",
    auth_header: dict[str, str],
) -> None:
    """Test retrieving the admin prompt."""
    test_app.db_manager.get_admin_setting = AsyncMock(
        return_value="Prompt here"
    )
    response = test_client.get("/admin/prompt", headers=auth_header)
    assert response.status_code == 200
    assert response.json() == {"prompt": "Prompt here"}


def test_set_prompt(
    test_client: TestClient,
    test_app: "EvaApp",
    auth_header: dict[str, str],
) -> None:
    """Test setting the admin prompt."""
    test_app.db_manager.set_admin_setting = AsyncMock()
    response = test_client.post(
        "/admin/prompt", json={"prompt": "New prompt"}, headers=auth_header
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_documents(
    test_client: TestClient,
    auth_header: dict[str, str],
) -> None:
    """Test listing documents in the RAG folder."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        Path(tmpdirname, "doc1.txt").write_text("Test doc", encoding="utf-8")
        Path(tmpdirname, "doc2.txt").write_text("Test doc 2", encoding="utf-8")
        with patch.object(settings, "rag_docs_folder", tmpdirname):
            response = test_client.get("/admin/documents", headers=auth_header)
            assert response.status_code == 200
            files = response.json()["documents"]
            assert "doc1.txt" in files
            assert "doc2.txt" in files


def test_upload_document(
    test_client: TestClient,
    auth_header: dict[str, str],
) -> None:
    """Test uploading a document to the RAG folder."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        with patch.object(settings, "rag_docs_folder", tmpdirname):
            files = {"file": ("uploaded.txt", b"content")}
            response = test_client.post(
                "/admin/documents", files=files, headers=auth_header
            )
            assert response.status_code == 200
            assert response.json() == {"status": "uploaded"}
            assert Path(tmpdirname, "uploaded.txt").exists()


def test_delete_document_success(
    test_client: TestClient,
    auth_header: dict[str, str],
) -> None:
    """Test deleting a document from the RAG folder."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        file_path = Path(tmpdirname, "to_delete.txt")
        file_path.write_text("delete me", encoding="utf-8")
        with patch.object(settings, "rag_docs_folder", tmpdirname):
            response = test_client.delete(
                f"/admin/documents/{file_path.name}", headers=auth_header
            )
            assert response.status_code == 200
            assert not file_path.exists()


def test_delete_document_not_found(
    test_client: TestClient,
    auth_header: dict[str, str],
) -> None:
    """Test deleting a document that does not exist."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        with patch.object(settings, "rag_docs_folder", tmpdirname):
            response = test_client.delete(
                "/admin/documents/nonexistent.txt", headers=auth_header
            )
            assert response.status_code == 404


@pytest.mark.asyncio
async def test_reload_docs(
    test_client: TestClient,
    test_app: "EvaApp",
    auth_header: dict[str, str],
) -> None:
    """Test reloading documents in the RAG manager."""
    test_app.rag_manager.reload_documents = AsyncMock()
    response = test_client.post("/admin/reload", headers=auth_header)
    assert response.status_code == 200
    assert response.json() == {"status": "reloaded"}


@pytest.mark.asyncio
async def test_list_conversations(
    test_client: TestClient,
    test_app: "EvaApp",
    auth_header: dict[str, str],
) -> None:
    """Test listing conversations in the database."""
    test_app.db_manager.list_conversations = AsyncMock(
        return_value=["c1", "c2"]
    )
    test_app.db_manager.count_conversations = AsyncMock(return_value=2)
    response = test_client.get("/admin/conversations", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["conversations"] == ["c1", "c2"]
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_download_conversation(
    test_client: TestClient,
    test_app: "EvaApp",
    auth_header: dict[str, str],
) -> None:
    """Test downloading a conversation from the database."""
    test_app.db_manager.get_conversation_messages = AsyncMock(
        return_value=[{"role": "user", "content": "hi"}]
    )
    response = test_client.get(
        "/admin/conversations/123/download", headers=auth_header
    )
    assert response.status_code == 200
    assert response.json()["conversation_id"] == "123"


@pytest.mark.asyncio
async def test_delete_conversation_success(
    test_client: TestClient,
    test_app: "EvaApp",
    auth_header: dict[str, str],
) -> None:
    """Test deleting a conversation from the database."""
    test_app.db_manager.delete_conversation = AsyncMock()
    response = test_client.delete(
        "/admin/conversations/abc", headers=auth_header
    )
    assert response.status_code == 200
    assert response.json() == {"status": "deleted"}


@pytest.mark.asyncio
async def test_delete_conversation_failure(
    test_client: TestClient,
    test_app: "EvaApp",
    auth_header: dict[str, str],
) -> None:
    """Test deleting a conversation that fails."""
    test_app.db_manager.delete_conversation = AsyncMock(
        side_effect=Exception("boom")
    )
    response = test_client.delete(
        "/admin/conversations/xyz", headers=auth_header
    )
    assert response.status_code == 500
    assert "Failed to delete conversation" in response.json()["detail"]
