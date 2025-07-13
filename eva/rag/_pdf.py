# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""PDF Loader using PyMuPDF."""

# pyright: reportReturnType=false,reportMissingTypeStubs=false
# pyright: reportUnknownVariableType=false,reportUnknownMemberType=false
# pylint: disable=no-self-use, broad-exception-caught,too-many-branches
# pylint: disable=too-many-try-statements,too-few-public-methods
import logging
from pathlib import Path

import pymupdf  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class PDFLoader:
    """Class to load and process PDF files using PyMuPDF."""

    @staticmethod
    def load(file_path: Path) -> str:
        """Read PDF files using PyMuPDF.

        Parameters
        ----------
        file_path : Path
            The path to the PDF file to read.

        Returns
        -------
        str
            The content of the PDF file formatted as text.
        """
        doc: pymupdf.Document | None = None
        try:
            doc = pymupdf.open(file_path)
            content_parts = _extract_pdf_content(doc, file_path)
            return "\n".join(content_parts)

        except Exception as e:
            logger.error("Error opening PDF %s: %s", file_path, e)
            return (
                f"PDF Document: {file_path.name}\n"
                "Error: Could not open or process PDF file"
            )
        finally:
            if doc:
                try:
                    doc.close()
                except Exception as e:  # pragma: no cover
                    logger.warning("Error closing PDF document: %s", e)


def _extract_pdf_content(doc: pymupdf.Document, file_path: Path) -> list[str]:
    """Extract all content from PDF document."""
    content_parts = [f"PDF Document: {file_path.name}"]

    # Add metadata
    metadata_parts = _extract_pdf_metadata(doc)
    content_parts.extend(metadata_parts)

    content_parts.append(f"Pages: {len(doc)}")
    content_parts.append("")  # Empty line separator

    # Extract content from each page
    for page_num in range(len(doc)):
        page_content = _extract_page_content(doc, page_num)
        content_parts.extend(page_content)

    return content_parts


def _extract_pdf_metadata(doc: pymupdf.Document) -> list[str]:
    """Extract metadata from PDF document."""
    metadata_parts: list[str] = []

    try:
        metadata = doc.metadata
        if metadata and isinstance(metadata, dict):  # pyright: ignore
            for key, label in [
                ("title", "Title"),
                ("author", "Author"),
                ("subject", "Subject"),
            ]:
                if metadata.get(key):  # pragma: no cover
                    metadata_parts.append(f"{label}: {metadata[key]}")
    except Exception as e:  # pragma: no cover
        logger.warning("Could not extract metadata: %s", e)

    return metadata_parts


def _extract_page_content(
    doc: pymupdf.Document,
    page_num: int,
) -> list[str]:
    """Extract content from a single PDF page."""
    page_content = []

    try:
        page = doc[page_num]

        # Extract text
        text_content = _extract_page_text(page, page_num)
        page_content.extend(text_content)

        # Extract tables
        table_content = _extract_page_tables(page, page_num)
        page_content.extend(table_content)

    except Exception as e:
        logger.warning("Error processing page %d: %s", page_num + 1, e)
        page_content.extend(
            [
                f"--- Page {page_num + 1} ---",
                "Error: Could not extract content from this page",
                "",
            ]
        )

    return page_content


def _extract_page_text(
    page: pymupdf.Page,
    page_num: int,
) -> list[str]:
    """Extract text content from a PDF page."""
    text_content = []

    try:
        text = page.get_text()  # pyright: ignore
        if text and text.strip():  # pragma: no branch
            text_content.extend(
                [
                    f"--- Page {page_num + 1} ---",
                    text.strip(),
                    "",  # Empty line between pages
                ]
            )
    except Exception as e:  # pragma: no cover
        logger.warning(
            "Error extracting text from page %d: %s", page_num + 1, e
        )

    return text_content


def _extract_page_tables(
    page: pymupdf.Page,
    page_num: int,
) -> list[str]:
    """Extract table content from a PDF page."""
    table_content = []

    try:
        tables = page.find_tables()  # pyright: ignore
        if tables.tables:
            for table_num, table in enumerate(tables.tables):  # pyright: ignore
                table_data = _extract_single_table(
                    table,  # pyright: ignore
                    table_num,
                    page_num,
                )
                table_content.extend(table_data)
                table_content.append("")  # Empty line after each table

    except Exception as e:
        logger.warning("Error finding tables on page %d: %s", page_num + 1, e)

    return table_content


def _extract_single_table(
    table: pymupdf.table.Table, table_num: int, page_num: int
) -> list[str]:
    """Extract data from a single table."""
    table_data = [f"Table {table_num + 1} on Page {page_num + 1}:"]

    try:
        extracted_data = table.extract()
        if extracted_data:  # pragma: no branch
            for row in extracted_data:
                if _is_valid_table_row(row):  # pyright: ignore
                    row_text = " | ".join(
                        str(cell or "").strip()  # pyright: ignore
                        for cell in row
                    )
                    table_data.append(row_text)
    except Exception as e:
        logger.warning(
            "Error extracting table %d from page %d: %s",
            table_num + 1,
            page_num + 1,
            e,
        )
        table_data.append("Error: Could not extract table data")

    return table_data


def _is_valid_table_row(row: pymupdf.table.TableRow) -> bool:
    """Check if a table row contains valid data (not empty)."""
    return row and any(c and str(c).strip() for c in row)  # pyright: ignore
