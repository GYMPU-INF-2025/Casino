from __future__ import annotations

import typing

from shared.internal import Snowflake

__all__ = ("decode_hook", "encode_hook")


def encode_hook(obj: typing.Any) -> typing.Any:
    if isinstance(obj, Snowflake):
        return int(obj)
    raise NotImplementedError(f"Objects of type {type} are not supported")


def decode_hook(t: type, obj: typing.Any) -> typing.Any:
    if t is Snowflake:
        return Snowflake(obj)
    raise NotImplementedError(f"Objects of type {type} are not supported")
