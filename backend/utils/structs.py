from __future__ import annotations

import typing

import msgspec

__all__ = ("convert_struct",)

T = typing.TypeVar("T", bound=msgspec.Struct)


def convert_struct(from_obj: msgspec.Struct, to_cls: type[T]) -> T:
    filtered_data = {
        k: from_obj.__getattribute__(k) for k in from_obj.__struct_fields__ if k in to_cls.__struct_fields__
    }
    return to_cls(**filtered_data)
