from __future__ import annotations

import msgspec

__all__ = ("BaseEvent", "UpdateMoney")


class BaseEvent(msgspec.Struct):
    @classmethod
    def event_name(cls) -> str:
        result = []
        for i, char in enumerate(cls.__name__):
            if char.isupper() and i != 0:
                result.append("_")
            result.append(char)
        return "".join(result).upper()


class UpdateMoney(BaseEvent):
    money: int
