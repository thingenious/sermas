# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Utility functions for cleaning and validating JSON responses."""
# pylint: disable=too-complex,too-many-try-statements
# flake8: noqa: C901

import json
import re
from typing import Any


def clean_and_validate_json(response_text: str) -> dict[str, Any]:
    """Clean, validate, and verify JSON response structure.

    This function attempts to parse a JSON response, validate its structure,
    and ensure it matches the expected schema. It handles common issues like
    duplicate JSON objects, missing keys, and incorrect types.

    Parameters
    ----------
    response_text : str
        The raw response text to clean and validate.

    Returns
    -------
    dict[str, Any]
        A validated JSON object with the expected structure.

    Raises
    ------
    ValueError
        If the response cannot be parsed as valid JSON or
        does not match the expected schema.
    """
    # Try to parse as-is first
    try:
        data = json.loads(response_text)
        validate_schema(data)
        return data
    except json.JSONDecodeError:
        pass
    except ValueError as schema_error:
        # If it's a schema validation error, re-raise it
        if "JSON object" in str(schema_error) or "segments" in str(
            schema_error
        ):
            raise schema_error

    # If direct parsing failed, try to extract first valid JSON
    # pylint: disable=too-many-try-statements
    try:
        brace_count = 0
        first_json_end = -1

        for i, char in enumerate(response_text):
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    first_json_end = i + 1
                    break

        if first_json_end > 0:
            first_json = response_text[:first_json_end]
            data = json.loads(first_json)
            validate_schema(data)
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    # Try to find JSON using regex as last resort
    try:
        # Look for JSON pattern starting with {"segments":
        json_pattern = r'\{"segments":\s*\[.*?\]\s*\}'
        match = re.search(json_pattern, response_text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            validate_schema(data)
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    # If all parsing attempts failed, provide detailed error
    raise ValueError(
        "Could not parse valid JSON with expected schema from response. "
        f"Response: {response_text[:200]}..."
    )


def fix_spacing_after_punctuation(text: str) -> str:
    """Fix spacing after punctuation.

    Ensure proper spacing after punctuation like ., ?, !
    if followed by a letter or number.

    Example: "Paris.It" => "Paris. It"

    Parameters
    ----------
    text : str
        The input text to fix.

    Returns
    -------
    str
        The text with fixed spacing after punctuation.
    """
    return re.sub(r"([.!?])([A-Za-z0-9])", r"\1 \2", text)


# Optional: Add a repair function for common issues
def attempt_json_repair(response_text: str) -> str:
    """Try to repair common JSON issues.

    This function attempts to clean up the response text by removing
    duplicate JSON objects, ensuring it starts with a '{' and ends with a '}'.

    Parameters
    ----------
    response_text : str
        The raw response text to clean.

    Returns
    -------
    str
        A cleaned version of the response text that should be valid JSON.
    """
    # Remove duplicate JSON objects (your specific issue)
    if response_text.count('{"segments"') > 1:
        # Find the first complete JSON object
        first_segments_pos = response_text.find('{"segments"')
        if first_segments_pos != -1:
            # Find the matching closing brace
            brace_count = 0
            for i in range(first_segments_pos, len(response_text)):
                if response_text[i] == "{":
                    brace_count += 1
                elif response_text[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        return response_text[first_segments_pos : i + 1]

    # Remove any text before the first {
    first_brace = response_text.find("{")
    if first_brace > 0:
        response_text = response_text[first_brace:]

    # Remove any text after the last }
    last_brace = response_text.rfind("}")
    if last_brace != -1 and last_brace < len(response_text) - 1:
        response_text = response_text[: last_brace + 1]

    return response_text


def validate_schema(data: Any) -> bool:
    """Validate that the JSON has the expected structure.

    Parameters
    ----------
    data : Any
        The parsed JSON data to validate.

    Returns
    -------
    bool
        True if the data matches the expected schema.

    Raises
    ------
    ValueError
        If the data does not match the expected schema.
    """
    if not isinstance(data, dict):
        raise ValueError("Response must be a JSON object")

    if "segments" not in data:
        raise ValueError("Missing required 'segments' key")

    segments: list[Any] = data["segments"]  # pyright: ignore
    if not isinstance(segments, list):
        raise ValueError("'segments' must be an array")

    if len(segments) == 0:  # pyright: ignore
        raise ValueError("'segments' array cannot be empty")

    for i, segment in enumerate(segments):  # pyright: ignore
        if not isinstance(segment, dict):
            raise ValueError(f"Segment {i} must be an object")

        if "content" not in segment:
            raise ValueError(f"Segment {i} missing 'content' key")

        if "emotion" not in segment:
            raise ValueError(f"Segment {i} missing 'emotion' key")
        if not isinstance(segment["content"], str):
            raise ValueError(f"Segment {i} 'content' must be a string")

        if not isinstance(segment["emotion"], str):
            raise ValueError(f"Segment {i} 'emotion' must be a string")

        if not segment["content"].strip():
            raise ValueError(f"Segment {i} 'content' cannot be empty")

    return True
