# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Module for loading various file types into strings."""

# pylint: disable=broad-exception-caught
# pylint: disable=too-many-try-statements,import-outside-toplevel
import json
import logging
from pathlib import Path
from typing import Any

from ._pdf import PDFLoader

logger = logging.getLogger(__name__)


def load_txt(file_path: Path) -> str:
    """Load a text file and return its content as a string.

    Parameters
    ----------
    file_path : Path
        The path to the text file to be loaded.

    Returns
    -------
    str
        The content of the text file as a string.
    """
    return file_path.read_text(encoding="utf-8")


def load_md(file_path: Path) -> str:
    """Load a Markdown file and return its content as a string.

    Parameters
    ----------
    file_path : Path
        The path to the Markdown file to be loaded.

    Returns
    -------
    str
        The content of the Markdown file as a string.
    """
    return file_path.read_text(encoding="utf-8")


def load_json(file_path: Path) -> str:
    """Load a JSON file and return its content as a pretty-formatted string.

    Parameters
    ----------
    file_path : Path
        The path to the JSON file to be loaded.

    Returns
    -------
    str
        The content of the JSON file as a pretty-formatted string.
    """
    # Return as pretty-formatted string for chunking/search
    data = json.loads(file_path.read_text(encoding="utf-8"))
    content_parts = [f"JSON File: {file_path.name}"]
    content_parts.append(_json_to_text(data))
    return "\n".join(content_parts)


def _json_to_text(obj: Any, prefix: str = "") -> str:
    """Convert JSON object to readable text."""
    parts: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():  # pyright: ignore
            if isinstance(value, (dict, list)):
                parts.append(f"{prefix}{key}:")
                parts.append(_json_to_text(value, prefix + "  "))
            else:
                parts.append(f"{prefix}{key}: {value}")
        return "\n".join(parts)
    if isinstance(obj, list):
        parts = []
        for i, item in enumerate(obj):  # pyright: ignore
            if isinstance(item, (dict, list)):  # pragma: no cover
                parts.append(f"{prefix}Item {i + 1}:")
                parts.append(_json_to_text(item, prefix + "  "))
            else:
                parts.append(f"{prefix}Item {i + 1}: {item}")
        return "\n".join(parts)
    return str(obj)  # pragma: no cover


def load_csv(file_path: Path) -> str:
    """Load a CSV file and return its content as a string.

    Parameters
    ----------
    file_path : Path
        The path to the CSV file to be loaded.

    Returns
    -------
    str
        The content of the CSV file as a string.

    Raises
    ------
    ImportError
        If the pandas library is not installed.
    """
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("pandas is required for CSV loading") from e
    df = pd.read_csv(file_path)  # pyright: ignore
    return df.to_csv(index=False)


def load_docx(file_path: Path) -> str:
    """Load a DOCX file and return its content as a string.

    Parameters
    ----------
    file_path : Path
        The path to the DOCX file to be loaded.

    Returns
    -------
    str
        The content of the DOCX file as a string.

    Raises
    ------
    ImportError
        If the python-docx library is not installed.
    """
    try:
        from docx import Document
    except ImportError as e:
        raise ImportError("python-docx is required for DOCX loading") from e
    doc = Document(str(file_path))
    return "\n".join(p.text for p in doc.paragraphs if p.text)


# pylint: disable=too-complex,too-many-locals
def load_odt(file_path: Path) -> str:
    """Read ODT files using odfpy.

    Parameters
    ----------
    file_path : Path
        The path to the ODT file to read.

    Returns
    -------
    str
        The content of the ODT file formatted as text.
    """
    try:
        from odf.opendocument import load  # type: ignore[import-untyped]
        from odf.table import (  # type: ignore[import-untyped]
            Table,  # pyright: ignore
            TableCell,  # pyright: ignore
            TableRow,  # pyright: ignore
        )
        from odf.text import P  # type: ignore[import-untyped]
    except ImportError:
        logger.error("odfpy not installed. Install with: pip install odfpy")
        return ""

    try:
        doc = load(file_path)
        content_parts = [f"ODT Document: {file_path.name}"]
        # Extract paragraphs
        for paragraph in doc.getElementsByType(P):  # pyright: ignore
            text = _extract_text_from_element(paragraph)
            if text:  # pragma: no branch
                content_parts.append(text)

        # Extract tables
        for table in doc.getElementsByType(Table):  # pyright: ignore
            content_parts.append("\nTable:")
            for row in table.getElementsByType(TableRow):  # pyright: ignore
                cells = row.getElementsByType(TableCell)  # pyright: ignore
                row_cells: list[str] = []
                for cell in cells:  # pyright: ignore
                    cell_text = _extract_text_from_element(cell)
                    row_cells.append(cell_text if cell_text else "")

                row_text = " | ".join(row_cells)
                if row_text.strip():  # pragma: no branch
                    content_parts.append(row_text)

        return "\n".join(content_parts)

    except Exception as e:  # pragma: no cover
        logger.error("Error reading ODT file %s: %s", file_path, str(e))
        return ""


LOADER_MAP = {
    ".txt": load_txt,
    ".md": load_md,
    ".json": load_json,
    ".csv": load_csv,
    ".docx": load_docx,
    ".odt": load_odt,
    ".pdf": PDFLoader.load,
}

SUPPORTED_EXTENSIONS = set(LOADER_MAP.keys())


# pylint: disable=too-few-public-methods
class DocumentLoader:
    """Class to load various document types into strings."""

    @staticmethod
    def load(file_path: Path) -> str:
        """Load a file and return its content as a string.

        Parameters
        ----------
        file_path : Path
            The path to the file to be loaded.

        Returns
        -------
        str
            The content of the file as a string.

        Raises
        ------
        FileNotFoundError
            If the specified file does not exist.
        ValueError
            If the file type is not supported.
        """
        suffix = file_path.suffix.lower()
        if not file_path.exists():
            raise FileNotFoundError(str(file_path))
        if suffix not in LOADER_MAP:
            raise ValueError(f"Unsupported file type: {suffix}")
        return LOADER_MAP[suffix](file_path)


def _extract_text_from_element(element: Any) -> str:
    """Extract plain text from ODF elements.

    Parameters
    ----------
    element : Any
        The ODF element from which to extract text.

    Returns
    -------
    str
        The extracted text content.
    """
    text_content: list[str] = []
    # Handle text nodes directly
    if hasattr(element, "data"):
        return element.data

    # Recursively extract text from child elements
    if hasattr(element, "childNodes"):  # pragma: no branch
        for child in element.childNodes:
            if hasattr(child, "data"):
                text_content.append(child.data)
            else:  # pragma: no cover
                # Recursively get text from nested elements
                nested_text = _extract_text_from_element(child)
                if nested_text:
                    text_content.append(nested_text)

    return "".join(text_content).strip()
