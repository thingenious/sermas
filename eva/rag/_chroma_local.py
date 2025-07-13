# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""ChromaDB local RAG Manager implementation."""

# pylint: disable=too-many-try-statements,broad-exception-caught,duplicate-code
import asyncio
import uuid as uuid_lib
from pathlib import Path
from typing import Any, Optional

import chromadb
import chromadb.utils.embedding_functions as ef
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection  # pyright: ignore
from chromadb.api.types import EmbeddingFunction, Metadata
from chromadb.config import Settings

from ._base import BaseRAGManager


class ChromaLocalRAGManager(BaseRAGManager):
    """ChromaDB local RAG Manager implementation."""

    def __init__(
        self,
        local: bool = True,
        persist_directory: str = "chroma_db",
        collection_name: str = "eve_rag",
        documents_root: str = "documents",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        super().__init__()
        self.local = local
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.documents_root = documents_root
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.collection: Optional[Collection] = None
        self.embedding_function: Optional[EmbeddingFunction[Any]] = None
        self.client: Optional[ClientAPI] = None

    async def initialize(self) -> None:
        """Initialize ChromaDB client and collection.

        Raises
        ------
        RuntimeError
            If the ChromaDB client fails to initialize
            or collection creation fails.
        """
        try:
            # Initialize ChromaDB client
            self.client, self.collection, self.embedding_function = (
                self._initialize(
                    persist_directory=self.persist_directory,
                    collection_name=self.collection_name,
                )
            )
            await self.load_documents(self.documents_root)
        except Exception as e:  # pragma: no cover
            raise RuntimeError(f"Failed to initialize ChromaDB: {e}") from e

    async def reload_documents(self) -> None:
        """Reload documents into ChromaDB.

        Raises
        ------
        RuntimeError
            If the RAGManager is not initialized or loading documents fails.
        """
        if not self.collection:
            await self.initialize()
        if not self.collection:
            raise RuntimeError(
                "RAGManager not initialized. Call initialize() first."
            )
        if not self.client:
            raise RuntimeError("ChromaDB client not initialized.")
        self.client.reset()
        await self.initialize()
        await self.load_documents(self.documents_root)
        self.logger.info("Collection reloaded from disk.")

    async def search(
        self, query: str, n_results: int = 3
    ) -> list[dict[str, Any]]:
        """Asynchronous search method.

        Parameters
        ----------
        query : str
            The query string to search for.
        n_results : int, optional
            Number of results to return, by default 3.

        Returns
        -------
        list[dict[str, Any]]
            List of search results with metadata.
        """
        results = await asyncio.get_event_loop().run_in_executor(
            None, self._search, query, n_results
        )
        return results

    async def load_documents(self, documents_path: str) -> None:
        """Asynchronously load documents into ChromaDB.

        Parameters
        ----------
        documents_path : str
            Path to the directory containing documents to load.

        Raises
        ------
        RuntimeError
            If loading documents fails.
        """
        await asyncio.get_event_loop().run_in_executor(
            None, self._load_documents, documents_path
        )

    # pylint: disable=no-self-use
    def _initialize(
        self,
        persist_directory: str,
        collection_name: str,
    ) -> tuple[ClientAPI, Collection, EmbeddingFunction[Any]]:
        """Initialize ChromaDB client and collection.

        Parameters
        ----------
        persist_directory : str
            Directory to persist the ChromaDB database.
        collection_name : str
            Name of the collection to create or access.

        Returns
        -------
        tuple[ClientAPI, Collection, EmbeddingFunction[Any]]
            Tuple containing the ChromaDB client,
            the collection, and the embedding function.

        Raises
        ------
        RuntimeError
            If the ChromaDB client fails to initialize
            or collection creation fails.
        """
        try:
            # Initialize ChromaDB client
            settings = Settings(
                is_persistent=True,
                persist_directory=persist_directory,
                allow_reset=True,
                anonymized_telemetry=False,
            )
            client = chromadb.Client(settings=settings)
            embedding_function = ef.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2",
            )
            try:
                collection = client.get_collection(
                    collection_name,
                    embedding_function=embedding_function,  # type: ignore
                )
            except Exception:
                collection = client.create_collection(
                    name=collection_name,
                    embedding_function=embedding_function,  # type: ignore
                )

            # Create collection if it doesn't exist
        except Exception as e:  # pragma: no cover
            raise RuntimeError(f"Failed to initialize ChromaDB: {e}") from e
        return client, collection, embedding_function

    # pylint: disable=too-many-locals
    def _load_documents(self, documents_path: str) -> None:
        """Load documents into ChromaDB.

        Parameters
        ----------
        documents_path : str
            Path to the directory containing documents to load.

        Raises
        ------
        RuntimeError
            If loading documents fails.
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
            content = self.extract_text_from_file(file_path)
            if content:  # pragma: no branch
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
                self.collection.add(
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

    def _search(self, query: str, n_results: int = 3) -> list[dict[str, Any]]:
        """Search using ChromaDB vector search.

        Parameters
        ----------
        query : str
            The query string to search for.
        n_results : int, optional
            Number of results to return, by default 3.

        Returns
        -------
        list[dict[str, Any]]
            List of search results with metadata.

        Raises
        ------
        RuntimeError
            If the RAGManager is not initialized.
        """
        if not self.collection:
            raise RuntimeError(
                "RAGManager not initialized. Call initialize() first."
            )

        results = self.collection.query(
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
