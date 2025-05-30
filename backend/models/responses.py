"""Public responses for responding to http requests."""

from __future__ import annotations

import typing

import msgspec

if typing.TYPE_CHECKING:
    from backend.internal import Snowflake

__all__ = ("PublicUser", "Success", "Test")


class Test(msgspec.Struct):
    """Testing purposes."""

    test: str


class Success(msgspec.Struct):
    """Testing purposes."""

    message: str = msgspec.field(default="Success!")


class PublicUser(msgspec.Struct):
    """Public User struct."""

    id: Snowflake
    username: str
    money: int
