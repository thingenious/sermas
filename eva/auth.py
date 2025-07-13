# SPDX-License-Identifier: Apache-2.0.
# Copyright (c) 2024 - 2025 Thingenious.

"""Authentication utilities for WebSocket connections in FastAPI."""

import logging

from fastapi import WebSocket

from eva.config import settings

logger = logging.getLogger(__name__)


def get_token_from_cookie(
    websocket: WebSocket,
    cookie_name: str = "token",
) -> tuple[str | None, str | None]:
    """Extract the access token from the WebSocket cookies.

    Parameters
    ----------
    websocket : WebSocket
        The WebSocket connection from which to extract the token.
    cookie_name : str, optional
        The name of the cookie to look for, by default "token".

    Returns
    -------
    str | None
        The access token if present in the cookies, otherwise None.
    """
    return websocket.cookies.get(cookie_name), None


def get_token_from_query_params(
    websocket: WebSocket, key_name: str = "token"
) -> tuple[str | None, str | None]:
    """Extract the access token from the WebSocket query parameters.

    Parameters
    ----------
    key_name : str, optional
        The name of the query parameter to look for, by default "token".
    websocket : WebSocket
        The WebSocket connection from which to extract the token.

    Returns
    -------
    str | None
        The access token if present, otherwise None.
    """
    return websocket.query_params.get(key_name, None), None


def get_token_from_auth_header(
    websocket: WebSocket,
    _: str,
) -> tuple[str | None, str | None]:
    """Extract the access token from the WebSocket authorization header.

    Parameters
    ----------
    websocket : WebSocket
        The WebSocket connection from which to extract the token.

    Returns
    -------
    str | None
        The access token if present in the authorization header,
        otherwise None.
    """
    auth_header = websocket.headers.get("authorization")
    if not auth_header:
        return None, None
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1], None
    return None, None


def get_token_from_subprotocol(
    websocket: WebSocket,
    _prefix: str = "token",  # pylint: disable=unused-argument
) -> tuple[str | None, str | None]:
    """Extract the access token from the WebSocket subprotocol.

    Parameters
    ----------
    websocket : WebSocket
        The WebSocket connection from which to extract the token.

    Returns
    -------
    str | None
        The access token if present in the subprotocol, otherwise None.
    """
    sec_protocol = websocket.headers.get("sec-websocket-protocol")
    if not sec_protocol:
        return None, None
    sec_parts = [p.strip() for p in sec_protocol.split(",")]
    sec_parts = sec_protocol.split(",")
    if len(sec_parts) != 2:
        return None, None
    token = sec_parts[1].strip().split(":")[-1]
    return token, sec_parts[0]


def extract_ws_token(
    websocket: WebSocket, *, subprotocol_prefix: str = "token"
) -> tuple[str | None, str | None]:
    """Extract the WebSocket access token from various sources.

    Parameters
    ----------
    websocket : WebSocket
        The WebSocket connection from which to extract the token.
    subprotocol_prefix : str, optional
        The prefix to look for in the subprotocol, by default "token".

    Returns
    -------
    str | None
        The access token if found in any of the sources,
        otherwise None.
    """
    # Order of priority can be adjusted as needed
    for fn in (
        get_token_from_auth_header,
        get_token_from_subprotocol,
        get_token_from_query_params,
        get_token_from_cookie,
    ):
        token, subprotocol = fn(websocket, subprotocol_prefix)
        if token:
            return token, subprotocol
    return None, None


def verify_ws_token(token: str) -> bool:
    """Verify the WebSocket access token.

    Parameters
    ----------
    token : str
        The access token to verify.

    Returns
    -------
    bool
        True if the token is valid, False otherwise.
    """
    # For now, just compare with the app's API key
    return token == settings.chat_api_key
