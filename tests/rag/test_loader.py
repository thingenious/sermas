# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Tests for the DocumentLoader class in the eva.rag.loader module."""

# pyright: reportUnusedImport=false,reportPrivateUsage=false
# pylint: disable=missing-return-doc,missing-param-doc,missing-yield-doc
# pylint: disable=missing-function-docstring,missing-class-docstring
# pylint: disable=import-outside-toplevel,too-few-public-methods
# pylint: disable=unused-argument,invalid-name,no-self-use
from pathlib import Path

import pytest

from eva.rag.loader import DocumentLoader, _extract_text_from_element


@pytest.fixture(name="loader")
def loader_fixture() -> DocumentLoader:
    """Fixture to create a DocumentLoader instance."""
    return DocumentLoader()


@pytest.fixture(name="tmp_txt_file")
def tmp_txt_file_fixture(tmp_path: Path) -> Path:
    """Fixture to create a temporary text file."""
    file = tmp_path / "doc.txt"
    file.write_text("Hello, world!")
    return file


@pytest.fixture(name="tmp_md_file")
def tmp_md_file_fixture(tmp_path: Path) -> Path:
    """Fixture to create a temporary Markdown file."""
    file = tmp_path / "doc.md"
    file.write_text("# Heading\n\nBody text")
    return file


@pytest.fixture(name="tmp_json_file")
def tmp_json_file_fixture(tmp_path: Path) -> Path:
    """Fixture to create a temporary JSON file."""
    file = tmp_path / "doc.json"
    file.write_text('{"foo": "bar", "num": 42}')
    return file


@pytest.fixture(name="tmp_csv_file")
def tmp_csv_file_fixture(tmp_path: Path) -> Path:
    """Fixture to create a temporary CSV file."""
    file = tmp_path / "doc.csv"
    file.write_text("name,age\nAlice,30\nBob,22")
    return file


def test_load_txt_file(loader: DocumentLoader, tmp_txt_file: Path) -> None:
    """Test loading a text file."""
    content = loader.load(tmp_txt_file)
    assert "Hello, world!" in content


def test_load_md_file(loader: DocumentLoader, tmp_md_file: Path) -> None:
    """Test loading a Markdown file."""
    content = loader.load(tmp_md_file)
    assert "# Heading" in content


def test_load_json_file(loader: DocumentLoader, tmp_json_file: Path) -> None:
    """Test loading a JSON file."""
    content = loader.load(tmp_json_file)
    assert "foo" in content and "bar" in content


def test_load_csv_file(loader: DocumentLoader, tmp_csv_file: Path) -> None:
    """Test loading a CSV file."""
    content = loader.load(tmp_csv_file)
    assert "Alice,30" in content


def test_load_unsupported_filetype(
    loader: DocumentLoader, tmp_path: Path
) -> None:
    """Test loading an unsupported file type."""
    file = tmp_path / "file.unsupported"
    file.write_text("data")
    with pytest.raises(ValueError):
        loader.load(file)


def test_load_missing_file(loader: DocumentLoader, tmp_path: Path) -> None:
    """Test loading a non-existent file."""
    file = tmp_path / "doesnotexist.txt"
    with pytest.raises(FileNotFoundError):
        loader.load(file)


def test_load_docx_file(loader: DocumentLoader, tmp_path: Path) -> None:
    """Test loading a DOCX file."""
    pytest.importorskip("docx")
    from docx import Document

    file = tmp_path / "doc.docx"
    doc = Document()
    doc.add_paragraph("Docx text")
    doc.save(str(file))
    content = loader.load(file)
    assert "Docx text" in content


def test_load_odt_file(loader: DocumentLoader, tmp_path: Path) -> None:
    """Test loading an ODT file."""
    pytest.importorskip("odf.opendocument")
    from odf.opendocument import OpenDocumentText  # type: ignore
    from odf.text import P  # type: ignore

    file = tmp_path / "doc.odt"
    doc = OpenDocumentText()
    doc.text.addElement(P(text="ODT text"))  # pyright: ignore
    doc.save(str(file))  # pyright: ignore
    content = loader.load(file)
    assert "ODT text" in content


def test_pdf_loader(tmp_path: Path) -> None:
    """Test loading a PDF file."""
    pytest.importorskip("pymupdf")
    from fpdf import FPDF

    pdf_file = tmp_path / "sample.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "Hello PDF", ln=True)
    pdf.output(str(pdf_file))

    # Should not crash and must mention file name
    out = DocumentLoader.load(pdf_file)
    assert "PDF Document: sample.pdf" in out


def test_loader_txt(tmp_path: Path) -> None:
    """Test loading a text file."""
    path = tmp_path / "sample.txt"
    path.write_text("hello world")
    assert DocumentLoader.load(path) == "hello world"


def test_loader_md(tmp_path: Path) -> None:
    """Test loading a Markdown file."""
    path = tmp_path / "sample.md"
    path.write_text("# Header\nBody")
    assert DocumentLoader.load(path) == "# Header\nBody"


def test_loader_json(tmp_path: Path) -> None:
    """Test loading a JSON file."""
    path = tmp_path / "sample.json"
    path.write_text('{"foo": 123, "bar": [1,2]}')
    result = DocumentLoader.load(path)
    assert "foo: 123" in result
    assert "bar:" in result


def test_loader_nonexistent(tmp_path: Path) -> None:
    """Test loading a non-existent file."""
    with pytest.raises(FileNotFoundError):
        DocumentLoader.load(tmp_path / "missing.txt")


def test_loader_unsupported(tmp_path: Path) -> None:
    """Test loading an unsupported file type."""
    path = tmp_path / "file.unsupported"
    path.write_text("data")
    with pytest.raises(ValueError):
        DocumentLoader.load(path)


def test_loader_csv_import_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that loading a CSV file raises ImportError."""
    path = tmp_path / "file.csv"
    path.write_text("a,b\n1,2")
    monkeypatch.setitem(__import__("sys").modules, "pandas", None)
    from importlib import reload

    import eva.rag.loader as loader_mod

    reload(loader_mod)
    with pytest.raises(ImportError):
        loader_mod.load_csv(path)


def test_loader_docx_import_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that loading a DOCX file raises ImportError."""
    path = tmp_path / "file.docx"
    monkeypatch.setitem(__import__("sys").modules, "docx", None)
    from importlib import reload

    import eva.rag.loader as loader_mod

    reload(loader_mod)
    with pytest.raises(ImportError):
        loader_mod.load_docx(path)


def test_loader_odt_import_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that loading an ODT file raises ImportError."""
    path = tmp_path / "file.odt"
    monkeypatch.setitem(__import__("sys").modules, "odf.opendocument", None)
    from importlib import reload

    import eva.rag.loader as loader_mod

    reload(loader_mod)
    # Should not raise, just log and return ""
    assert loader_mod.load_odt(path) == ""


def test_extract_text_from_element_basic() -> None:
    """Test basic text extraction from an element."""

    class Dummy:
        data = "foo"

    elem = Dummy()
    assert _extract_text_from_element(elem) == "foo"


def test_extract_text_from_element_recursive() -> None:
    """Test recursive text extraction from an element with child nodes."""

    class Leaf:
        data = "bar"

    class Parent:
        childNodes = [Leaf(), Leaf()]

    p = Parent()
    assert _extract_text_from_element(p) == "barbar"


# pylint: disable=too-complex
def test_loader_odt_table(  # noqa: C901
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test loading an ODT file with a table using a mocked odfpy API."""
    path = tmp_path / "file.odt"
    path.write_text("does not matter")

    class DummyP:
        def __init__(self, txt: str) -> None:
            """Initialize a dummy paragraph with text."""
            self.data = txt

    class DummyCell:
        def __init__(self, txt: str) -> None:
            """Initialize a dummy cell with text."""
            self.childNodes = [DummyP(txt)]

    class DummyRow:
        def getElementsByType(self, typ: str) -> list[DummyCell]:
            """Simulate the ODF table row structure."""
            return [DummyCell("cell1"), DummyCell("cell2")]

    class DummyTable:
        def getElementsByType(self, typ: str) -> list[DummyRow]:
            """Simulate the ODF table structure."""
            return [DummyRow()]

    class DummyDoc:
        def getElementsByType(
            self, typ: str
        ) -> list[DummyP | DummyTable | DummyRow | DummyCell]:
            """Simulate the ODF document structure."""
            if typ.__name__ == "P":  # type: ignore
                return [DummyP("par1")]
            if typ.__name__ == "Table":  # type: ignore
                return [DummyTable()]
            if typ.__name__ == "TableRow":  # type: ignore
                return [DummyRow()]
            if typ.__name__ == "TableCell":  # type: ignore
                return [DummyCell("cellX")]
            return []

    class DummyODF:
        @staticmethod
        def load(p: Path) -> "DummyDoc":
            """Simulate loading an ODT document."""
            return DummyDoc()

    import types

    dummy_mod = types.SimpleNamespace(
        load=DummyODF.load,
        Table=type("Table", (), {}),
        TableCell=type("TableCell", (), {}),
        TableRow=type("TableRow", (), {}),
    )
    monkeypatch.setitem(
        __import__("sys").modules, "odf.opendocument", dummy_mod
    )
    monkeypatch.setitem(__import__("sys").modules, "odf.table", dummy_mod)
    monkeypatch.setitem(
        __import__("sys").modules,
        "odf.text",
        types.SimpleNamespace(P=type("P", (), {})),
    )
    from importlib import reload

    import eva.rag.loader as loader_mod

    reload(loader_mod)
    # Should include 'ODT Document', 'par1', 'Table:'
    result = loader_mod.load_odt(path)
    assert "ODT Document" in result
    assert "par1" in result
    assert "Table:" in result
