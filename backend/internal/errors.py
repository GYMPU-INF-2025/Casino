from __future__ import annotations

import enum
import typing


class WebsocketError(RuntimeError):
    """A base exception type for anything that can be thrown by the Websocket."""

    def __init__(self, *, reason: str) -> None:
        self.reason = reason

    reason: str
    """A string to explain the issue."""

    @typing.override
    def __str__(self) -> str:
        return self.reason


class WebsocketConnectionError(WebsocketError):
    """An exception thrown if a connection issue occurs."""

    @typing.override
    def __str__(self) -> str:
        return f"Failed to connect to client: {self.reason!r}"


class WebsocketCloseCode(enum.IntEnum):
    PROTOCOL_ERROR = 1_002

    UNKNOWN_OPCODE = 4001
    DECODE_ERROR = 4002
    NOT_AUTHENTICATED = 4003
    AUTHENTICATION_FAILED = 4004
    LOBBY_FULL = 4005
    INVALID_LOBBY = 4006


class WebsocketClientClosedConnectionError(WebsocketError):
    """An exception raised when the client closes the connection."""

    @typing.override
    def __init__(self, *, reason: str, code: int) -> None:
        self.reason = reason
        self.code = code

    code: int
    """Return the close code that was received."""

    @typing.override
    def __str__(self) -> str:
        return f"Client closed connection with code {self.code} ({self.reason})"


class WebsocketTransportError(WebsocketError):
    """An exception thrown if an issue occurs at the transport layer."""

    @typing.override
    def __str__(self) -> str:
        return f"Websocket transport error: {self.reason}"
