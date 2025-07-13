# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.
"""Test authentication-related functionality in the application."""
# mypy: disable-error-code="unused-ignore, arg-type"

# pyright: reportArgumentType=false
# pylint: disable=missing-return-doc,missing-param-doc,missing-yield-doc
# pylint: disable=missing-function-docstring,missing-class-docstring

import pytest

from eva.auth import (
    extract_ws_token,
    get_token_from_auth_header,
    get_token_from_cookie,
    get_token_from_query_params,
    get_token_from_subprotocol,
    verify_ws_token,
)


# pylint: disable=too-few-public-methods
class DummyWS:
    """Simple mock to simulate WebSocket object for auth extraction."""

    def __init__(
        self,
        cookies: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Initialize the dummy WebSocke."""
        self.cookies = cookies or {}
        self.query_params = query_params or {}
        self.headers = headers or {}


# --- Individual extractors ---


def test_get_token_from_cookie() -> None:
    """Test extracting token from WebSocket cookies."""
    ws = DummyWS(cookies={"token": "abc123"})
    assert get_token_from_cookie(ws)[0] == "abc123"
    ws = DummyWS(cookies={})
    assert get_token_from_cookie(ws)[0] is None


def test_get_token_from_query_params() -> None:
    """Test extracting token from WebSocket query parameters."""
    ws = DummyWS(query_params={"token": "xyz789"})
    assert get_token_from_query_params(ws)[0] == "xyz789"
    ws = DummyWS(query_params={})
    assert get_token_from_query_params(ws)[0] is None


def test_get_token_from_auth_header() -> None:
    """Test extracting token from WebSocket authorization header."""
    ws = DummyWS(headers={"authorization": "Bearer secret42"})
    assert get_token_from_auth_header(ws, "")[0] == "secret42"
    ws = DummyWS(headers={"authorization": "Token whatevar"})
    assert get_token_from_auth_header(ws, "")[0] is None
    ws = DummyWS(headers={})
    assert get_token_from_auth_header(ws, "")[0] is None


def test_get_token_from_subprotocol() -> None:
    """Test extracting token from WebSocket subprotocol header."""
    # Should parse "prefix, actualtoken"
    ws = DummyWS(headers={"sec-websocket-protocol": "myproto, subtok"})
    assert get_token_from_subprotocol(ws)[0] == "subtok"
    ws = DummyWS(headers={"sec-websocket-protocol": "myproto"})
    assert get_token_from_subprotocol(ws)[0] is None
    ws = DummyWS(headers={})
    assert get_token_from_subprotocol(ws)[0] is None


# --- Full extraction logic ---


def test_extract_ws_token_priority() -> None:
    """Test the full token extraction logic with priority order."""
    # 1. Auth header (priority)
    ws = DummyWS(
        headers={"authorization": "Bearer topsecret"},
        query_params={"token": "in_query"},
        cookies={"token": "in_cookie"},
    )
    assert extract_ws_token(ws)[0] == "topsecret"

    # 2. Subprotocol (second)
    ws = DummyWS(
        headers={"sec-websocket-protocol": "chat, fromsub"},
        query_params={"token": "fromquery"},
        cookies={"token": "fromcookie"},
    )
    assert extract_ws_token(ws)[0] == "fromsub"

    # 3. Query param
    ws = DummyWS(
        query_params={"token": "fromquery"},
        cookies={"token": "fromcookie"},
    )
    assert extract_ws_token(ws)[0] == "fromquery"

    # 4. Cookie
    ws = DummyWS(cookies={"token": "fromcookie"})
    assert extract_ws_token(ws)[0] == "fromcookie"

    # 5. None found
    ws = DummyWS()
    assert extract_ws_token(ws)[0] is None


def test_extract_ws_token_with_custom_subprotocol() -> None:
    """Test extracting token with a custom subprotocol prefix."""
    ws = DummyWS(headers={"sec-websocket-protocol": "chat, xyz"})
    token, proto = extract_ws_token(ws, subprotocol_prefix="token")
    assert token == "xyz"  # nosemgrep # nosec
    assert proto == "chat"


# --- Token verification (with monkeypatch) ---


def test_verify_ws_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test verifying WebSocket token against configured API key."""
    monkeypatch.setattr("eva.config.settings.chat_api_key", "supersecret")
    assert verify_ws_token("supersecret") is True
    assert verify_ws_token("notsecret") is False
