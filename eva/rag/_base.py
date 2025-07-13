# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Base class for RAG (Retrievel-Augmented Generation) managers."""

# pyright: reportReturnType=false
# pylint: disable=no-self-use, broad-exception-caught,too-many-try-statements
import asyncio
import logging
from pathlib import Path
from typing import Any, Protocol

from .loader import SUPPORTED_EXTENSIONS, DocumentLoader


class RAGManager(Protocol):
    """Protocol for a RAG manager."""

    async def initialize(self) -> None:
        """Initialize the RAG manager."""

    async def load_documents(self, documents_path: str) -> None:
        """Load documents into the RAG manager.

        Parameters
        ----------
        documents_path : str
            Path to the directory or file containing documents.
        """

    async def reload_documents(self) -> None:
        """Reload documents into the RAG manager."""

    async def search(
        self, query: str, n_results: int = 3
    ) -> list[dict[str, Any]]:
        """Search using the RAG manager.

        Parameters
        ----------
        query : str
            The search query.
        n_results : int, optional
            The number of results to return (default is 3).

        Returns
        -------
        list[dict[str, Any]]
            A list of search results, each containing relevant information.
        """


class BaseRAGManager(RAGManager):
    """Base class for RAG (Retrievel-Augmented Generation) managers."""

    def __init__(self) -> None:
        """Initialize the BaseRAGManager."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def _get_supported_files(self, path: Path) -> list[Path]:
        """Get all supported files from path.

        Parameters
        ----------
        path : Path
            The path to the file or directory.
        """
        if path.is_file():
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                return [path]  # pragma: no cover
            self.logger.warning("Unsupported file type: %s", path.suffix)
            return []
        if path.is_dir():
            files: list[Path] = []
            for ext in SUPPORTED_EXTENSIONS:
                files.extend(path.rglob(f"*{ext}"))
            return files
        raise ValueError(f"Invalid path: {path}")

    # pylint: disable=too-many-return-statements
    async def a_extract_text_from_file(self, file_path: Path) -> str:
        """Asynchronously extract text content from various file formats.

        Parameters
        ----------
        file_path : Path
            The path to the file to read.

        Returns
        -------
        str
            The extracted text content from the file.
        """
        try:
            future = asyncio.get_event_loop().run_in_executor(
                None, self.extract_text_from_file, file_path
            )
            await asyncio.sleep(0)  # Yield control to the event loop
            return await future
        except BaseException:
            self.logger.error("Error reading file %s", file_path)
            return ""

    def extract_text_from_file(self, file_path: Path) -> str:
        """Extract text content from various file formats.

        Parameters
        ----------
        file_path : Path
            The path to the file to read.

        Returns
        -------
        str
            The extracted text content from the file.
        """
        try:
            return DocumentLoader.load(file_path)
        except Exception as e:
            self.logger.error("Error loading file %s: %s", file_path, e)
            return ""

    # pylint: disable=no-self-use
    def split_text(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        """Text splitting with overlap.

        Parameters
        ----------
        text : str
            The text to split into chunks.
        chunk_size : int
            The size of each chunk.
        overlap : int
            The number of characters to overlap between chunks.

        Returns
        -------
        list[str]
            A list of text chunks.
        """
        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            if end < len(text):
                last_period = chunk.rfind(".")
                last_newline = chunk.rfind("\n")
                break_point = max(last_period, last_newline)

                if break_point > start + chunk_size // 2:
                    chunk = text[start : start + break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - overlap

            if start >= len(text):
                break

        return [chunk for chunk in chunks if chunk]
