import typing

import msgspec

__all__ = (
    "WebSocketPayload",
)

class WebSocketPayload(msgspec.Struct):
    
    op: int
    d: dict[str, typing.Any]
    s: int | None = msgspec.field(default=None)
    t: str | None = msgspec.field(default=None)
    
