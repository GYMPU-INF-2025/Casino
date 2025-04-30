"""Public responses for responding to http requests."""

from __future__ import annotations

import msgspec


class Test(msgspec.Struct):
    """Testing purposes."""

    test: str


class Success(msgspec.Struct):
    """Testing purposes."""

    message: str = msgspec.field(default="Success!")
