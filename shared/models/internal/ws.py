from __future__ import annotations

import typing

import msgspec

__all__ = ("IdentifyPayload", "WebSocketPayload")

if typing.TYPE_CHECKING:
    from shared.internal import Snowflake
    from shared.models.responses import PublicUser


class WebSocketPayload(msgspec.Struct):
    op: int
    d: dict[str, typing.Any]
    t: str | None = msgspec.field(default=None)


class IdentifyPayload(msgspec.Struct):
    token: str
