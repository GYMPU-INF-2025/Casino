from __future__ import annotations

import typing

import msgspec

__all__ = ("BaseEvent", "UpdateMoney")

from shared.models import responses
from shared.internal import snowflakes


class BaseEvent(msgspec.Struct):
    @classmethod
    def event_name(cls) -> str:
        result = []
        for i, char in enumerate(cls.__name__):
            if char.isupper() and i != 0:
                result.append("_")
            result.append(char)
        return "".join(result).upper()

class ReadyEvent(BaseEvent):
    user: responses.PublicUser
    client_id: snowflakes.Snowflake
    num_clients: int

class UpdateMoney(BaseEvent):
    money: int

class UpdateTake(BaseEvent):
    total: int
    stake: int
    take: int
    gamemode: int

class UpdateStep(BaseEvent):
    stake: int
    gamemode: int
    take: int

class UpdateGamemode(BaseEvent):
    gamemode: int