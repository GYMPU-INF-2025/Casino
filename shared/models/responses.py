"""Public responses for responding to http requests."""

from __future__ import annotations

import datetime
import typing

import msgspec

import datetime

from shared.internal import Snowflake

__all__ = ("ErrorResponse", "LoginResponse", "PublicUser", "Success", "Test")


class Test(msgspec.Struct):
    """Testing purposes."""

    test: str


class ErrorResponse(msgspec.Struct):
    """Response sent together with an error."""

    name: str
    message: str
    detail: str


class LoginResponse(msgspec.Struct):
    """Represents the token response after a successful login."""

    token: str
    expires_at: datetime.datetime


class Success(msgspec.Struct):
    """Testing purposes."""

    message: str = msgspec.field(default="Success!")


class PublicUser(msgspec.Struct):
    """Public User struct."""

    id: Snowflake
    username: str
    money: int


class PublicGameLobby(msgspec.Struct):
    """Public Game Lobby struct."""

    id: str
    full: bool
    max_clients: int
    num_clients: int
