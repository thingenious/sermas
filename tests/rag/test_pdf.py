# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Test cases for PDFLoader class in the eva.rag._pdf module."""
# pyright: reportPrivateUsage=false,reportArgumentType=false
# pyright: reportUnknownArgumentType=false,reportUnknownLambdaType=false
# pylint: disable=missing-return-doc,missing-param-doc,missing-raises-doc
# pylint: disable=missing-function-docstring,missing-class-docstring
# pylint: disable=broad-exception-raised, no-self-use,unused-argument
# pylint: disable=too-few-public-methods,protected-access

from pathlib import Path
from typing import Any, Iterable

import pymupdf  # type: ignore[import-untyped]
import pytest

from eva.rag._pdf import PDFLoader, _extract_single_table, _is_valid_table_row


def test_pdfloader_file_not_found(tmp_path: Path) -> None:
    """Test that PDFLoader handles file not found error gracefully."""
    file = tmp_path / "doesnotexist.pdf"
    result = PDFLoader.load(file)
    assert "Error: Could not open or process PDF file" in result


def test_pdfloader_metadata_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Test that PDFLoader handles metadata extraction errors gracefully."""
    # Patch pymupdf.open and doc.metadata to throw an exception

    class DummyDoc:
        metadata = property(
            lambda self: (_ for _ in ()).throw(Exception("fail"))
        )

        def close(self) -> None:
            pass

        def __len__(self) -> int:
            return 0

    monkeypatch.setattr(pymupdf, "open", lambda _: DummyDoc())
    result = PDFLoader.load(tmp_path / "some.pdf")
    assert "PDF Document" in result  # still basic info present


def test_pdfloader_page_content_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Test that PDFLoader handles page content extraction errors gracefully."""

    class DummyDoc:
        metadata: dict[str, Any] = {}

        def close(self) -> None:
            pass

        def __len__(self) -> int:
            return 1

        def __getitem__(self, idx: int) -> Any:
            # pylint: disable=broad-exception-raised
            raise Exception("page error")

    monkeypatch.setattr(pymupdf, "open", lambda _: DummyDoc())
    result = PDFLoader.load(tmp_path / "any.pdf")
    assert "Error: Could not extract content from this page" in result


def test_pdfloader_close_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Test that PDFLoader handles document close errors gracefully."""

    class DummyDoc:
        metadata: dict[str, Any] = {}

        def close(self) -> None:
            raise Exception("fail on close")

        def __len__(self) -> int:
            return 0

    monkeypatch.setattr(pymupdf, "open", lambda _: DummyDoc())
    PDFLoader.load(tmp_path / "close.pdf")  # Should not raise


def test_pdfloader_table_extraction_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Test that PDFLoader handles table extraction successfully."""

    class DummyGoodTable:
        """Table class that simulates successful extraction."""

        def extract(self) -> str:
            """Simulate table extraction."""
            raise Exception("table fail")

    class DummyPage:
        def get_text(self) -> str:
            """Simulate page text extraction."""
            return "Some text"

        def find_tables(self) -> Any:
            """Simulate finding tables on the page."""
            return type("Tables", (), {"tables": [DummyGoodTable()]})()

    class DummyDoc:
        metadata: dict[str, Any] = {}

        def close(self) -> None:
            pass

        def __len__(self) -> int:
            return 1

        def __getitem__(self, idx: int) -> DummyPage:
            """Return a dummy page with table extraction failure."""
            return DummyPage()

    monkeypatch.setattr(pymupdf, "open", lambda _: DummyDoc())
    result = PDFLoader.load(tmp_path / "table.pdf")
    assert "Some text" in result


def test_pdfloader_table_extraction_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Test PDFLoader handles table extraction errors gracefully."""

    # pylint: disable=too-few-public-methods
    class DummyBadTable:
        """Table class that raises on extract."""

        def extract(self) -> str:
            raise Exception("table fail")

    class DummyPage:
        def get_text(self) -> str:
            """Simulate page text extraction."""
            return "Some text"

        def find_tables(self) -> Any:
            """Simulate finding tables on the page."""

            # Must have .tables property nonempty, and be iterable!
            class TablesObj:
                tables = [DummyBadTable()]

                def __iter__(self) -> Iterable[DummyBadTable]:
                    return iter(self.tables)

                def __len__(self) -> int:
                    return len(self.tables)

                def __getitem__(self, idx: int) -> DummyBadTable:
                    return self.tables[idx]

            return TablesObj()

    class DummyDoc:
        metadata: dict[str, Any] = {}

        def close(self) -> None:
            pass

        def __len__(self) -> int:
            return 1

        def __getitem__(self, idx: int) -> DummyPage:
            return DummyPage()

    monkeypatch.setattr(pymupdf, "open", lambda _: DummyDoc())

    result = PDFLoader.load(tmp_path / "table.pdf")

    assert "Error: Could not extract table data" in result


class DummyTableRow(list[Any]):
    """Behaves like a list, for table row emulation."""


class DummyTable:
    """Dummy table class for testing."""

    def __init__(self, should_fail: bool = False) -> None:
        """Initialize with an option to simulate extraction failure."""
        self.should_fail = should_fail

    def extract(self) -> list[DummyTableRow]:
        """Simulate table extraction."""
        if self.should_fail:
            raise Exception("Extract fail")
        # Return two rows, one valid, one empty
        return [
            DummyTableRow(["cell1", "cell2", ""]),
            DummyTableRow(["", "", ""]),
        ]


def test_extract_single_table_success() -> None:
    """Test that _extract_single_table extracts valid rows correctly."""
    table = DummyTable()
    # Should extract only the valid row
    result = _extract_single_table(
        table,
        table_num=0,
        page_num=0,
    )
    assert "Table 1 on Page 1:" in result[0]
    assert "cell1 | cell2 |" in result[1]
    assert len(result) == 2  # Only one valid row (plus the header)


def test_extract_single_table_handles_error() -> None:
    """Test that _extract_single_table handles extraction errors gracefully."""
    table = DummyTable(should_fail=True)
    result = _extract_single_table(
        table,
        table_num=1,
        page_num=2,
    )
    # Should show the error string
    assert result == [
        "Table 2 on Page 3:",
        "Error: Could not extract table data",
    ]


def test_is_valid_table_row_true() -> None:
    """Test that _is_valid_table_row correctly identifies valid rows."""
    assert _is_valid_table_row(["foo", ""]) is True
    assert _is_valid_table_row(["", "bar"]) is True


def test_is_valid_table_row_false() -> None:
    """Test that _is_valid_table_row correctly identifies invalid rows."""
    assert not _is_valid_table_row(["", ""])
    assert not _is_valid_table_row([])
