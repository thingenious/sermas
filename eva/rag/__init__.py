# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""RAG related modules for EVA application."""

from eva.config import settings

from ._base import RAGManager
from ._chroma_local import ChromaLocalRAGManager
from ._chroma_remote import ChromaRemoteRAGManager


def get_rag_manager() -> RAGManager:
    """Get the RAG manager instance based on the configuration.

    Returns
    -------
    RAGManager
        An instance of the RAGManager configured for the application.
    """
    # just chroma for now
    if settings.chroma_local is True:
        return ChromaLocalRAGManager(
            persist_directory=settings.chroma_db_dir,
            collection_name=settings.chroma_collection_name,
            documents_root=settings.rag_docs_folder,
        )
    return ChromaRemoteRAGManager(
        host=settings.chroma_host,
        port=settings.chroma_port,
        collection_name=settings.chroma_collection_name,
        documents_root=settings.rag_docs_folder,
    )


__all__ = [
    "RAGManager",
    "get_rag_manager",
]
