# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.
# pyright: reportUnknownArgumentType=false
"""Test eva.llm.utils.*."""

from typing import Any

import pytest

from eva.llm.utils import (
    attempt_json_repair,
    clean_and_validate_json,
    fix_spacing_after_punctuation,
    validate_schema,
)


def test_fix_spacing_after_punctuation() -> None:
    """Test the fix_spacing_after_punctuation function."""
    assert (
        fix_spacing_after_punctuation("Hello.This is fine!")
        == "Hello. This is fine!"
    )
    assert (
        fix_spacing_after_punctuation("Wait!What?Really!")
        == "Wait! What? Really!"
    )
    assert fix_spacing_after_punctuation("No issues here.") == "No issues here."


def test_clean_and_validate_json_valid() -> None:
    """Test cleaning and validating a valid JSON response."""
    input_json = '{"segments":[{"content":"Hello world.","emotion":"neutral"}]}'
    result = clean_and_validate_json(input_json)
    assert result["segments"][0]["content"] == "Hello world."
    assert result["segments"][0]["emotion"] == "neutral"


def test_clean_and_validate_json_braced_prefix() -> None:
    """Test cleaning and validating JSON with a braced prefix."""
    input_text = (
        'Garbage {"segments":[{"content":"Paris.","emotion":"happy"}]} trailing'
    )
    result = clean_and_validate_json(input_text)
    assert result["segments"][0]["content"] == "Paris."
    assert result["segments"][0]["emotion"] == "happy"


def test_clean_and_validate_json_regex_fallback() -> None:
    """Test cleaning and validating JSON with regex fallback."""
    input_text = (
        "Some junk... "
        '{"segments": [{"content": "Test", "emotion": "neutral"}]} '
        "more junk"
    )
    input_text = input_text.replace("'", '"')
    result = clean_and_validate_json(input_text)
    assert result["segments"][0]["emotion"] == "neutral"


def test_clean_and_validate_json_fail() -> None:
    """Test that invalid JSON raises an error."""
    with pytest.raises(ValueError):
        clean_and_validate_json("No JSON here!")


def test_attempt_json_repair_duplicate() -> None:
    """Test repairing a response with duplicate JSON segments."""
    input_text = (
        '{"segments":[{"content":"A","emotion":"happy"}]}'
        "Garbage"
        '{"segments":[{"content":"B","emotion":"sad"}]}'
    )
    repaired = attempt_json_repair(input_text)
    assert '"content":"A"' in repaired
    assert '"content":"B"' not in repaired


def test_attempt_json_repair_prefix_suffix_trim() -> None:
    """Test repairing a response with prefix and suffix whitespace."""
    input_text = (
        'Noise... {"segments":[{"content":"X","emotion":"curious"}]} ...junk'
    )
    repaired = attempt_json_repair(input_text)
    assert repaired.strip().startswith("{")
    assert repaired.strip().endswith("}")
    assert '"content":"X"' in repaired


def test_validate_schema_success() -> None:
    """Test that a valid schema passes validation."""
    data = {"segments": [{"content": "Hi", "emotion": "neutral"}]}
    assert validate_schema(data) is True


@pytest.mark.parametrize(
    "invalid_data",
    [
        {},  # missing segments
        {"segments": "not a list"},
        {"segments": []},
        {"segments": [{}]},
        {"segments": [{"content": "", "emotion": "happy"}]},
        {"segments": [{"content": "Text"}]},  # missing emotion
    ],
)
def test_validate_schema_failures(invalid_data: dict[str, Any]) -> None:
    """Test that invalid schemas raise ValueError.

    Parameters
    ----------
    invalid_data : dict[str, Any]
        A dictionary representing invalid JSON data to test validation.
    """
    with pytest.raises(ValueError):
        validate_schema(invalid_data)
