# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""ChromaDB RAG Manager for handling document storage and retrieval."""

import uuid as uuid_lib
from pathlib import Path
from typing import Any, Optional

import chromadb.utils.embedding_functions as ef
from chromadb.api.async_client import AsyncClient
from chromadb.api.models.AsyncCollection import (  # pyright: ignore
    AsyncCollection,
)
from chromadb.api.types import Metadata
from chromadb.config import Settings

from ._base import BaseRAGManager


# pylint: disable=too-many-instance-attributes,too-many-locals,duplicate-code
class ChromaRemoteRAGManager(BaseRAGManager):  # pragma: no cover
    """ChromaDB remote RAG Manager implementation."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        collection_name: str = "eva_rag",
        model_name: str = "all-MiniLM-L6-v2",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        use_ssl: bool = False,
        documents_root: str = "documents",
    ):
        super().__init__()
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.documents_root = documents_root
        self.model_name = model_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.use_ssl = use_ssl
        self.collection: Optional[AsyncCollection] = None
        self.embedding_function: Optional[ef.EmbeddingFunction[Any]] = None
        self.client: Optional[AsyncClient] = None

    async def initialize(self) -> None:
        """Initialize ChromaDB async client and collection.

        Raises
        ------
        RuntimeError
            If the initialization fails due to
            connection issues or collection creation errors.
        """
        # pylint: disable=too-many-try-statements,broad-exception-caught
        try:
            # Initialize embedding function
            embedding_function = ef.SentenceTransformerEmbeddingFunction(
                self.model_name
            )
            self.embedding_function = embedding_function
            protocol = "https" if self.use_ssl else "http"
            settings = Settings(
                anonymized_telemetry=False,
                chroma_server_host=f"{protocol}://{self.host}",
                chroma_server_http_port=self.port,
                chroma_server_ssl_enabled=self.use_ssl,
                chroma_server_ssl_verify=False,
            )
            self.client = await AsyncClient.create(
                settings=settings,
            )
            # Get or create collection
            try:
                self.collection = await self.client.get_collection(
                    name=self.collection_name,
                    embedding_function=embedding_function,  # type: ignore
                )
                self.logger.info(
                    "Using existing collection: %s", self.collection_name
                )
            except Exception:
                # Collection doesn't exist, create it
                self.collection = await self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=embedding_function,  # type: ignore
                    metadata={"hnsw:space": "cosine"},
                )
                self.logger.info(
                    "Created new collection: %s",
                    self.collection_name,
                )

            self.logger.info(
                "ChromaDB RAG Manager initialized with async HTTP client"
            )
            await self.load_documents(self.documents_root)
        except Exception as e:
            self.logger.error("Failed to initialize ChromaDB: %s", e)
            raise RuntimeError(
                "Failed to initialize ChromaDB RAG Manager"
            ) from e

    async def load_documents(self, documents_path: str) -> None:
        """Load documents into ChromaDB asynchronously.

        Parameters
        ----------
        documents_path : str
            Path to the directory containing documents to load.

        Raises
        ------
        RuntimeError
            If the RAGManager is not initialized or no documents are found.
        """
        if not self.collection:
            raise RuntimeError(
                "RAGManager not initialized. Call initialize() first."
            )

        path = Path(documents_path)
        files = self._get_supported_files(path)

        documents: list[str] = []
        metadatas: list[Metadata] = []
        ids: list[str] = []

        for file_path in files:
            content = await self.a_extract_text_from_file(file_path)
            if content:
                chunks = self.split_text(
                    content, self.chunk_size, self.chunk_overlap
                )

                for i, chunk in enumerate(chunks):
                    doc_id = f"{file_path.stem}_{i}_{uuid_lib.uuid4().hex[:8]}"
                    documents.append(chunk)
                    metadatas.append(
                        {
                            "source": str(file_path),
                            "file_name": file_path.name,
                            "file_type": file_path.suffix.lower(),
                            "chunk_id": i,
                            "file_size": file_path.stat().st_size,
                            "created_at": file_path.stat().st_mtime,
                        }
                    )
                    ids.append(doc_id)

        if documents:
            # Batch process documents asynchronously
            batch_size = 100  # Process in batches to avoid memory issues

            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i : i + batch_size]
                batch_metadatas = metadatas[i : i + batch_size]
                batch_ids = ids[i : i + batch_size]
                await self.collection.add(
                    documents=batch_docs,
                    metadatas=batch_metadatas,
                    ids=batch_ids,
                )
                batch = i // batch_size + 1
                total_batches = (len(documents) + batch_size - 1) // batch_size
                to_log = f"Processed batch {batch}/{total_batches}"
                self.logger.info(to_log)

            to_log = (
                f"Loaded {len(documents)} document "
                f"chunks from {len(files)} files"
            )
            self.logger.info(to_log)
        else:
            self.logger.warning("No documents found to load")

    async def reload_documents(self) -> None:
        """Reload documents into ChromaDB asynchronously.

        This method clears the existing collection and reloads documents
        from the configured documents root directory.

        Raises
        ------
        RuntimeError
            If the RAGManager is not initialized or the collection is not set.
        """
        if not self.collection:
            raise RuntimeError(
                "RAGManager not initialized. Call initialize() first."
            )

        await self.delete_collection()
        await self.load_documents(self.documents_root)

    async def search(
        self, query: str, n_results: int = 3
    ) -> list[dict[str, Any]]:
        """Search ChromaDB asynchronously.

        Parameters
        ----------
        query : str
            The query string to search for.
        n_results : int, optional
            The number of results to return, by default 3.

        Returns
        -------
        list[dict[str, Any]]
            A list of dictionaries containing search results with content,
            metadata, score, and id.

        Raises
        ------
        RuntimeError
            If the RAGManager is not initialized.
        """
        if not self.collection:
            raise RuntimeError(
                "RAGManager not initialized. Call initialize() first."
            )

        results = await self.collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        formatted_results: list[dict[str, Any]] = []
        if results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                formatted_results.append(
                    {
                        "content": results["documents"][0][i],
                        "metadata": (
                            results["metadatas"][0][i]
                            if results["metadatas"]
                            else {}
                        ),
                        "score": (
                            1 - results["distances"][0][i]
                            if results["distances"]
                            else 1.0
                        ),
                        "id": (
                            results["ids"][0][i]
                            if results.get("ids")
                            else f"result_{i}"
                        ),
                    }
                )

        return formatted_results

    async def delete_collection(self) -> None:
        """Delete the collection."""
        if self.client and self.collection:
            await self.client.delete_collection(name=self.collection_name)
            self.logger.info("Deleted collection: %s", self.collection_name)

    async def get_collection_info(self) -> dict[str, Any]:
        """Get collection statistics.

        Returns
        -------
        dict[str, Any]
            A dictionary containing collection name, count of documents,
            and embedding model name.

        Raises
        ------
        RuntimeError
            If the RAGManager is not initialized or the collection is not set.
        """
        if not self.collection:
            raise RuntimeError(
                "RAGManager not initialized. Call initialize() first."
            )
        if not self.client:
            raise RuntimeError(
                "ChromaDB client not initialized. Call initialize() first."
            )
        count = await self.collection.count()
        return {
            "name": self.collection_name,
            "count": count,
            "embedding_model": self.model_name,
        }
