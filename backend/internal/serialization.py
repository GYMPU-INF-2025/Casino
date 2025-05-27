"""Functionality to parse json payloads to our own structs and parsing structs to json."""

from __future__ import annotations

import functools
import inspect
import typing

import msgspec.json
import sanic
from sanic.exceptions import BadRequest

__all__ = ("deserialize", "serialize")

from backend.internal.hooks import decode_hook
from backend.internal.hooks import encode_hook

encoder = msgspec.json.Encoder(enc_hook=encode_hook)


P = typing.ParamSpec("P")


def serialize(
    *, status_code: int = 200
) -> typing.Callable[
    [typing.Callable[P, typing.Awaitable[msgspec.Struct]]], typing.Callable[P, typing.Awaitable[sanic.HTTPResponse]]
]:
    """Serialize the returned `msgspec.Struct` into json format."""

    def decorator(
        func: typing.Callable[P, typing.Awaitable[msgspec.Struct]],
    ) -> typing.Callable[P, typing.Awaitable[sanic.HTTPResponse]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> sanic.HTTPResponse:
            result = await func(*args, **kwargs)

            if isinstance(result, msgspec.Struct):
                return sanic.raw(body=encoder.encode(result), status=status_code, content_type="application/json")

            raise TypeError(f"{func.__name__} should return msgspec.Struct, but returned {type(result).__name__}")

        return wrapper

    return decorator


R = typing.TypeVar("R")


def deserialize() -> typing.Callable[
    [typing.Callable[P, typing.Awaitable[R]]], typing.Callable[P, typing.Awaitable[R]]
]:
    """Parse request body from json to a `msgspec.Struct`.

    Detects the first parameter annotated with a msgspec.Struct subclass,
    decodes the request body (JSON) into that struct, and injects it
    into **kwargs for the wrapped Sanic handler.
    """

    def decorator(func: typing.Callable[P, typing.Awaitable[R]]) -> typing.Callable[P, typing.Awaitable[R]]:
        sig = inspect.signature(func)
        type_hints = typing.get_type_hints(func)

        target_name: str | None = None
        target_type: type[msgspec.Struct] | None = None

        for name in sig.parameters:
            ann = type_hints.get(name)
            if isinstance(ann, type) and issubclass(ann, msgspec.Struct):
                target_name, target_type = name, ann
                break

        if target_name is None or target_type is None:
            return func

        decoder = msgspec.json.Decoder(target_type, dec_hook=decode_hook)

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            request: sanic.Request | None = None

            if args and isinstance(args[0], sanic.Request):
                request = args[0]
            elif "request" in kwargs and isinstance(kwargs["request"], sanic.Request):
                request = kwargs["request"]
            else:
                for value in (*args, *kwargs.values()):
                    if isinstance(value, sanic.Request):
                        request = value
                        break

            if request is None:
                raise RuntimeError("Could not locate a sanic.Request object to read the body from.")

            try:
                struct_obj = decoder.decode(request.body)
            except msgspec.DecodeError as exc:
                raise BadRequest(f"Malformed JSON: {exc}") from exc

            kwargs[target_name] = struct_obj
            return await func(*args, **kwargs)

        return wrapper

    return decorator
