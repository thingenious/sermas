# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.
# pylint: disable=unused-argument
"""Admin API for the EVA application."""

from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Header,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse, JSONResponse

from eva.config import settings
from eva.db import DatabaseManager
from eva.rag import RAGManager


def get_db_manager(request: Request) -> DatabaseManager:
    """Get the database manager from the request's app state.

    Parameters
    ----------
    request : Request
        The FastAPI request object.

    Returns
    -------
    DatabaseManager
        The database manager instance from the app state.
    """
    return request.app.db_manager


def get_rag_manager(request: Request) -> RAGManager:
    """Get the RAG manager from the request's app state.

    Parameters
    ----------
    request : Request
        The FastAPI request object.

    Returns
    -------
    RAGManager
        The RAG manager instance from the app state.
    """
    return request.app.rag_manager


def admin_auth(authorization: str | None = Header(default=None)) -> None:
    """Bearer Token authentication for admin routes.

    Parameters
    ----------
    authorization : str, optional
        The Authorization header value.

    Raises
    ------
    HTTPException
        If the authorization header is missing or invalid.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    expected = f"Bearer {settings.admin_api_key}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("", response_class=HTMLResponse, include_in_schema=False)
@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_admin_panel() -> HTMLResponse:
    """Serve the admin panel HTML page.

    Returns
    -------
    HTMLResponse
        The HTML content of the admin panel.
    """
    html_path = Path(__file__).parent / "static" / "admin.html"
    if not html_path.exists():
        return HTMLResponse("<h2>Not found</h2>", status_code=404)
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@router.get("/prompt")
async def get_prompt(
    _: str = Depends(admin_auth),
    db: DatabaseManager = Depends(get_db_manager),  # noqa: B008
) -> dict[str, str]:
    """Get the admin prompt setting.

    Parameters
    ----------
    db : DatabaseManager
        The database manager dependency.

    Returns
    -------
    dict[str, str]
        A dictionary containing the prompt setting.
    """
    prompt = await db.get_admin_setting("prompt")
    return {"prompt": prompt or ""}


@router.post("/prompt")
async def set_prompt(
    prompt: str = Body(..., embed=True),
    _: str = Depends(admin_auth),
    db: DatabaseManager = Depends(get_db_manager),  # noqa: B008
) -> dict[str, str]:
    """Set the admin prompt setting.

    Parameters
    ----------
    prompt : str
        The prompt text to set.
    db : DatabaseManager
        The database manager dependency.

    Returns
    -------
    dict[str, str]
        A dictionary indicating the status of the operation.
    """
    await db.set_admin_setting("prompt", prompt)
    return {"status": "ok"}


@router.get("/documents")
async def list_docs(
    _: str = Depends(admin_auth),
) -> dict[str, list[str]]:
    """List all documents in the RAG documents folder.

    Returns
    -------
    dict[str, list[str]]
        A dictionary containing a list of document filenames.
    """
    files = [
        f.name for f in Path(settings.rag_docs_folder).iterdir() if f.is_file()
    ]
    return {"documents": files}


@router.post("/documents")
async def upload_doc(
    file: UploadFile = File(...),  # noqa: B008
    _: str = Depends(admin_auth),
) -> dict[str, str]:  # noqa: B008
    """Upload a document to the RAG documents folder.

    Parameters
    ----------
    file : UploadFile
        The file to upload.

    Returns
    -------
    dict[str, str]
        A dictionary indicating the status of the upload.

    Raises
    ------
    HTTPException
        If no file is provided or if the upload fails.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    dest = Path(settings.rag_docs_folder) / file.filename
    with open(dest, "wb") as f:
        f.write(await file.read())
    return {"status": "uploaded"}


@router.delete("/documents/{filename}")
async def delete_doc(
    filename: str,
    _: str = Depends(admin_auth),
) -> dict[str, str]:
    """Delete a document from the RAG documents folder.

    Parameters
    ----------
    filename : str
        The name of the file to delete.

    Returns
    -------
    dict[str, str]
        A dictionary indicating the status of the deletion.

    Raises
    ------
    HTTPException
        If the file does not exist.
    """
    path = Path(settings.rag_docs_folder) / filename
    if path.exists():
        path.unlink()
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="File not found")


@router.post("/reload")
async def reload_docs(
    _: str = Depends(admin_auth),
    rag_manager: RAGManager = Depends(get_rag_manager),  # noqa: B008
) -> dict[str, str]:
    """Reload documents in the RAG manager.

    Parameters
    ----------
    rag_manager : RAGManager
        The RAG manager dependency.

    Returns
    -------
    dict[str, str]
        A dictionary indicating the status of the reload operation.
    """
    await rag_manager.reload_documents()
    return {"status": "reloaded"}


# List conversations
@router.get("/conversations")
async def list_conversations(
    _: str = Depends(admin_auth),
    db: DatabaseManager = Depends(get_db_manager),  # noqa: B008
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """List conversations with pagination.

    Parameters
    ----------
    db : DatabaseManager
        The database manager dependency.
    limit : int, optional
        The maximum number of conversations to return (default is 100).
    offset : int, optional
        The number of conversations to skip before starting
        to collect the result set (default is 0).

    Returns
    -------
    dict[str, Any]
        A dictionary containing the list of conversations,
        total count, limit, and offset.

    Raises
    ------
    HTTPException
        If the limit is less than 1 or the offset is negative.
    """
    if limit < 1 or offset < 0:
        raise HTTPException(
            status_code=400, detail="Limit must be >= 1 and offset must be >= 0"
        )
    conversations = await db.list_conversations(limit=limit, offset=offset)
    total = await db.count_conversations()
    return {
        "conversations": conversations,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# Download a conversation
@router.get("/conversations/{conversation_id}/download")
async def download_conversation(
    conversation_id: str,
    _: str = Depends(admin_auth),
    db: DatabaseManager = Depends(get_db_manager),  # noqa: B008
) -> JSONResponse:
    """Download a conversation by its ID.

    Parameters
    ----------
    conversation_id : str
        The ID of the conversation to download.
    db : DatabaseManager
        The database manager dependency.

    Returns
    -------
    JSONResponse
        A JSON response containing the conversation messages.

    Raises
    ------
    HTTPException
        If the conversation is not found.
    """
    messages = await db.get_conversation_messages(conversation_id, None)
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return JSONResponse(
        content={"conversation_id": conversation_id, "messages": messages}
    )


# Delete a conversation
@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    _: str = Depends(admin_auth),
    db: DatabaseManager = Depends(get_db_manager),  # noqa: B008
) -> dict[str, str]:
    """Delete a conversation by its ID.

    Parameters
    ----------
    conversation_id : str
        The ID of the conversation to delete.
    db : DatabaseManager
        The database manager dependency.

    Returns
    -------
    dict[str, str]
        A dictionary indicating the status of the deletion.

    Raises
    ------
    HTTPException
        If the operation fails or the conversation does not exist.
    """
    try:
        await db.delete_conversation(conversation_id)
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete conversation: {str(e)}"
        ) from e
