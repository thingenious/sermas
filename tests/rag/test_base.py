# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Tests for BaseRAGManager class."""
# pyright: reportPrivateUsage=false
# pylint: disable=missing-return-doc,missing-param-doc,missing-yield-doc
# pylint: disable=missing-function-docstring,protected-access,no-self-use

from pathlib import Path

import pytest

from eva.rag._base import BaseRAGManager


@pytest.fixture(name="base_manager")
def base_manager_fixture() -> BaseRAGManager:
    """Create a BaseRAGManager instance for testing."""
    return BaseRAGManager()  # type: ignore[abstract]


@pytest.mark.asyncio
async def test_manager_extract_text(
    tmp_path: Path,
    base_manager: BaseRAGManager,
) -> None:
    """Test that BaseRAGManager can extract text from a file."""
    file = tmp_path / "q.txt"
    file.write_text("async test")
    # sync version
    assert base_manager.extract_text_from_file(file) == "async test"
    # async version
    assert await base_manager.a_extract_text_from_file(file) == "async test"


def test_manager_get_supported_files(
    tmp_path: Path,
    base_manager: BaseRAGManager,
) -> None:
    """Test that BaseRAGManager finds supported files."""
    a = tmp_path / "1.md"
    b = tmp_path / "2.json"
    a.write_text("a")
    b.write_text("b")
    found = {f.name for f in base_manager._get_supported_files(tmp_path)}
    assert "1.md" in found and "2.json" in found


def test_get_supported_files_invalid_path(base_manager: BaseRAGManager) -> None:
    """Test that _get_supported_files raises ValueError for invalid path."""
    with pytest.raises(ValueError):
        base_manager._get_supported_files(Path("doesnotexist"))


@pytest.mark.asyncio
async def test_a_extract_text_from_file(
    tmp_path: Path,
    base_manager: BaseRAGManager,
) -> None:
    """Test that a_extract_text_from_file works with various file types."""
    # Uses a simple text file
    file = tmp_path / "hello.txt"
    file.write_text("Some text here")
    result = await base_manager.a_extract_text_from_file(file)
    assert isinstance(result, str)
    assert "Some text here" in result


def test_extract_text_from_file_txt(
    tmp_path: Path,
    base_manager: BaseRAGManager,
) -> None:
    """Test extracting text from a simple text file."""
    file = tmp_path / "a.txt"
    file.write_text("X")
    assert base_manager.extract_text_from_file(file) == "X"


def test_extract_text_from_file_json(
    tmp_path: Path,
    base_manager: BaseRAGManager,
) -> None:
    """Test extracting text from a JSON file."""
    file = tmp_path / "a.json"
    file.write_text('{"foo": "bar"}')
    result = base_manager.extract_text_from_file(file)
    assert "foo: bar" in result


def test_extract_text_from_file_unsupported(
    tmp_path: Path,
    base_manager: BaseRAGManager,
) -> None:
    """Test extracting text from an unsupported file type."""
    file = tmp_path / "a.unsupported"
    file.write_text("should not work")
    result = base_manager.extract_text_from_file(file)
    assert result == ""


def test_split_text_empty(
    base_manager: BaseRAGManager,
) -> None:
    """Test splitting empty text."""
    assert base_manager.split_text("", chunk_size=10, overlap=2) == []


def test_get_supported_files_file_unsupported(
    tmp_path: Path,
    base_manager: BaseRAGManager,
) -> None:
    """Test that _get_supported_files returns empty for unsupported file."""
    file = tmp_path / "file.unsupported"
    file.write_text("irrelevant")
    result = base_manager._get_supported_files(file)
    assert not result


def test_get_supported_files_dir_with_only_unsupported(
    tmp_path: Path,
    base_manager: BaseRAGManager,
) -> None:
    """Test that _get_supported_files returns empty for unsupported files."""
    (tmp_path / "one.unsupported").write_text("a")
    (tmp_path / "two.weird").write_text("b")
    result = base_manager._get_supported_files(tmp_path)
    assert not result


def test_get_supported_files_invalid(base_manager: BaseRAGManager) -> None:
    """Test that _get_supported_files raises ValueError for invalid paths."""

    # Path that is neither file nor dir: simulate with a mock
    class FakePath:
        """Fake path object that is neither file nor directory."""

        def is_file(self) -> bool:
            """Return False to simulate a non-file."""
            return False

        def is_dir(self) -> bool:
            """Return False to simulate a non-directory."""
            return False

    with pytest.raises(ValueError):
        base_manager._get_supported_files(FakePath())  # type: ignore


@pytest.mark.asyncio
async def test_a_extract_text_from_file_exception(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    base_manager: BaseRAGManager,
) -> None:
    """Test that a_extract_text_from_file handles exceptions."""
    file = tmp_path / "will_crash.txt"
    file.write_text("fail")
    # Patch extract_text_from_file to always raise
    monkeypatch.setattr(
        base_manager,
        "extract_text_from_file",
        lambda _: (_ for _ in ()).throw(ValueError("fail")),  # pyright: ignore
    )
    result = await base_manager.a_extract_text_from_file(file)
    assert result == ""


def test_extract_text_from_file_loader_exception(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    base_manager: BaseRAGManager,
) -> None:
    """Test that extract_text_from_file handles exceptions."""
    file = tmp_path / "will_fail.txt"
    file.write_text("fail")
    monkeypatch.setattr(
        "eva.rag._base.DocumentLoader.load",
        lambda _: (_ for _ in ()).throw(Exception("fail")),  # pyright: ignore
    )
    result = base_manager.extract_text_from_file(file)
    assert result == ""


def test_split_text_one_chunk(
    base_manager: BaseRAGManager,
) -> None:
    """Test splitting text that is smaller than chunk size."""
    # Text smaller than chunk_size
    text = "abc"
    result = base_manager.split_text(text, 10, 0)
    assert result == ["abc"]


def test_split_text_breakpoints(
    base_manager: BaseRAGManager,
) -> None:
    """Test splitting text at breakpoints."""
    # . and \n at various places
    text = "Sentence. More sentence\nEvan more."
    # Should split in a way that finds the period/newline
    result = base_manager.split_text(text, 12, 2)
    assert all(isinstance(chunk, str) for chunk in result)
    assert any("." in chunk or "\n" in chunk for chunk in result)
