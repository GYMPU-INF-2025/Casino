"""Snowflake id utility."""

from __future__ import annotations

import datetime
import os
import threading
import time
import typing

if typing.TYPE_CHECKING:
    import collections.abc

EPOCH: typing.Final[datetime.timedelta] = datetime.timedelta(seconds=1_420_070_400)  # Custom epoch: Jan 1, 2015 UTC
TIMESTAMP_SHIFT: typing.Final[int] = 22
WORKER_ID_SHIFT: typing.Final[int] = 12
SEQUENCE_MASK: typing.Final[int] = 0xFFF
WORKER_ID_MASK: typing.Final[int] = 0x3FF


def epoch_to_datetime(epoch: int) -> datetime.datetime:
    """Convert the epoch used for snowflakes to a datetime object."""
    return datetime.datetime.fromtimestamp(epoch / 1_000, datetime.UTC) + EPOCH


def datetime_to_epoch(timestamp: datetime.datetime) -> int:
    """Convert a datetime object into the epoch used for snowflakes."""
    return int((timestamp - EPOCH).timestamp() * 1_000)


@typing.final
class Snowflake(int):
    """A concrete representation of a unique ID.

    This object can be treated as a regular [`int`] for most purposes.
    """

    __slots__: collections.abc.Sequence[str] = ()

    @property
    def created_at(self) -> datetime.datetime:
        """When the object was created."""
        epoch = self >> TIMESTAMP_SHIFT
        return epoch_to_datetime(epoch)

    @property
    def internal_worker_id(self) -> int:
        """ID of the worker that created this snowflake."""
        return (self >> WORKER_ID_SHIFT) & WORKER_ID_MASK

    @property
    def sequence(self) -> int:
        """Increment of system when this object was made."""
        return self & SEQUENCE_MASK

    @classmethod
    def from_datetime(cls, timestamp: datetime.datetime) -> Snowflake:
        """Get a snowflake object from a datetime object."""
        return cls.from_data(timestamp, 0, 0)

    @classmethod
    def min(cls) -> Snowflake:
        """Minimum value for a snowflake."""
        return cls(0)

    @classmethod
    def max(cls) -> Snowflake:
        """Maximum value for a snowflake."""
        return cls((1 << 63) - 1)

    @classmethod
    def from_data(cls, timestamp: datetime.datetime, worker_id: int, sequence: int) -> Snowflake:
        """Convert the pieces of info that comprise an ID into a Snowflake."""
        return cls(
            (datetime_to_epoch(timestamp) << TIMESTAMP_SHIFT)
            | ((worker_id & WORKER_ID_MASK) << WORKER_ID_SHIFT)
            | (sequence & SEQUENCE_MASK)
        )


class _SnowflakeGenerator:
    def __init__(self) -> None:
        self._seq = 0
        self._worker_id: int = int(os.getenv("WORKER_ID", "1"))
        self._lock = threading.Lock()
        self._last_timestamp: float = -1

    def __call__(self) -> Snowflake:
        with self._lock:
            ts = time.time()

            if ts == self._last_timestamp:
                self._seq = (self._seq + 1) & 0xFFF
            else:
                self._seq = 0

            self.last_timestamp = ts

            return Snowflake.from_data(datetime.datetime.fromtimestamp(ts, datetime.UTC), self._worker_id, self._seq)


generate_snowflake = _SnowflakeGenerator()

Snowflakeish = Snowflake | int
"""Type hint for a value that resembles a `Snowflake` object functionally.

This is a value that is `Snowflake`-ish.

A value is `Snowflake`-ish if casting it to an `int` allows it to be cast to
a `Snowflake`.

The valid types for this type hint are:

- `int`
- `Snowflake`
"""
