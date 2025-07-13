# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Test cases for ChromaLocalRAGManager implementation."""

# pylint: disable=missing-return-doc,missing-param-doc,missing-yield-doc
# pylint: disable=missing-function-docstring,import-outside-toplevel
# pyright: reportUnknownArgumentType=false,reportUnknownLambdaType=false
# pyright: reportUnknownVariableType=false
import os
from pathlib import Path

import pytest

from eva.rag._chroma_local import ChromaLocalRAGManager


@pytest.fixture(name="chroma_manager")
def chroma_manager_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> ChromaLocalRAGManager:
    """Create a ChromaLocalRAGManager instance with dummy embedding."""
    import chromadb.utils.embedding_functions as ef

    # pylint: disable=too-few-public-methods
    class DummyEmbeddingFunction:
        """Dummy embedding function that returns fixed vectors."""

        # pylint: disable=redefined-builtin
        def __call__(self, input: list[str]) -> list[list[float]]:
            # Return a vector of length 3, value based on text length
            #  (just for deterministic variety)
            return [[float(len(t)) % 10 for _ in range(3)] for t in input]

    # Patch the factory to always return our dummy
    monkeypatch.setattr(
        ef,
        "SentenceTransformerEmbeddingFunction",
        lambda *args, **kwargs: DummyEmbeddingFunction(),
    )

    manager = ChromaLocalRAGManager(
        persist_directory=str(tmp_path / "chroma_db"),
        documents_root=str(tmp_path / "documents"),
    )
    os.makedirs(manager.documents_root, exist_ok=True)
    return manager


@pytest.mark.asyncio
async def test_end_to_end_index_and_search(
    chroma_manager: ChromaLocalRAGManager,
) -> None:
    """Test end-to-end indexing and searching functionality."""
    # 1. Create a sample file to index
    file = Path(chroma_manager.documents_root) / "file.txt"
    file.write_text("Cats are beautiful animals. Dogs are loyal companions.")

    # 2. Initialize and load the document
    await chroma_manager.initialize()

    # 3. Search for 'cats'
    results = await chroma_manager.search("cats", n_results=2)
    assert isinstance(results, list)
    assert any("cats" in r["content"].lower() for r in results)
    # 4. Search for something not present
    results2 = await chroma_manager.search("hamster", n_results=2)
    assert results2 == [] or all(
        "hamster" not in r["content"].lower() for r in results2
    )


@pytest.mark.asyncio
async def test_multiple_files_indexing(
    chroma_manager: ChromaLocalRAGManager,
) -> None:
    """Test indexing and searching across multiple files."""
    # Write multiple files

    (Path(chroma_manager.documents_root) / "alpha.txt").write_text(
        "Alpha alpha.", encoding="utf-8"
    )
    (Path(chroma_manager.documents_root) / "beta.txt").write_text(
        "Beta beta.", encoding="utf-8"
    )
    (Path(chroma_manager.documents_root) / "gamma.txt").write_text(
        "Gamma gamma.", encoding="utf-8"
    )
    await chroma_manager.initialize()
    results = await chroma_manager.search("beta")
    assert any("beta" in r["content"].lower() for r in results)


@pytest.mark.asyncio
async def test_empty_directory(chroma_manager: ChromaLocalRAGManager) -> None:
    """Test behavior when loading an empty directory."""
    await chroma_manager.initialize()
    # No exception, nothing to index, search returns nothing
    results = await chroma_manager.search("anything")
    assert results == []


@pytest.mark.asyncio
async def test_search_before_init_raises(tmp_path: Path) -> None:
    """Test that searching before initialization raises an error."""
    manager = ChromaLocalRAGManager(
        persist_directory=str(tmp_path / "chromadb")
    )
    with pytest.raises(RuntimeError):
        await manager.search("foo")


@pytest.mark.asyncio
async def test_load_before_init_raises(tmp_path: Path) -> None:
    """Test that loading documents before initialization raises an error."""
    manager = ChromaLocalRAGManager(
        persist_directory=str(tmp_path / "chromadb")
    )
    with pytest.raises(RuntimeError):
        await manager.load_documents(str(tmp_path))
