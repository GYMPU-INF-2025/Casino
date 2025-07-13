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


class MinesChangeStake(BaseEvent):
    amount: int

class MinesMineClicked(BaseEvent):
    x: int
    y: int

class MinesMineClickedResponse(BaseEvent):
    x: int
    y: int
    multiplier: float

class MinesGameOver(BaseEvent):
    x: int
    y: int

class MinesRestartGame(BaseEvent):
    pass

class MinesChashout(BaseEvent):
    pass

class MinesChashoutResponse(BaseEvent):
    balance: int

class MinesStartGame(BaseEvent):
    pass
