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

class DoStep(BaseEvent):
    stake: int
    take: int
    step: int

class DoStepResponse(BaseEvent):
    take: int

class UpdateGamemode(BaseEvent):
    gamemode: int

class UpdateMultiplier(BaseEvent):
    multiplier: float
    step_text: int

class UpdateMultiplierResponse(BaseEvent):
    multiplier: float
    step_text: int

class UpdateTotal(BaseEvent):
    total: int