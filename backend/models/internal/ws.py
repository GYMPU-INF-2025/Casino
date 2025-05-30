from __future__ import annotations

import typing

import msgspec

__all__ = ("IdentifyPayload", "ReadyPayload", "WebSocketPayload")

if typing.TYPE_CHECKING:
    from backend.internal import Snowflake
    from backend.models.responses import PublicUser


class WebSocketPayload(msgspec.Struct):
    op: int
    d: dict[str, typing.Any]
    t: str | None = msgspec.field(default=None)


class IdentifyPayload(msgspec.Struct):
    token: str


class ReadyPayload(msgspec.Struct):
    user: PublicUser
    client_id: Snowflake
    num_clients: int
