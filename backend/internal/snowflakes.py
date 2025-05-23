from __future__ import annotations

import abc
import datetime
import os
import threading
import time
import typing
import collections.abc

EPOCH: typing.Final[datetime.timedelta] = datetime.timedelta(seconds=1_420_070_400)  # Custom epoch: Jan 1, 2015 UTC
TIMESTAMP_SHIFT: typing.Final[int] = 22
WORKER_ID_SHIFT: typing.Final[int] = 12
SEQUENCE_MASK: typing.Final[int] = 0xFFF
WORKER_ID_MASK: typing.Final[int] = 0x3FF


def epoch_to_datetime(epoch: int) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(epoch / 1_000, datetime.timezone.utc) + EPOCH


def datetime_to_epoch(timestamp: datetime.datetime) -> int:
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
        epoch = (self >> TIMESTAMP_SHIFT)
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
    def min(cls) -> 'Snowflake':
        """Minimum value for a snowflake."""
        return cls(0)

    @classmethod
    def max(cls) -> 'Snowflake':
        """Maximum value for a snowflake."""
        return cls((1 << 63) - 1)

    @classmethod
    def from_data(cls, timestamp: datetime.datetime, worker_id: int, sequence: int) -> Snowflake:
        """Convert the pieces of info that comprise an ID into a Snowflake."""
        return cls(
            (datetime_to_epoch(timestamp) << TIMESTAMP_SHIFT) |
            ((worker_id & WORKER_ID_MASK) << WORKER_ID_SHIFT) |
            (sequence & SEQUENCE_MASK)
        )

class _SnowflakeGenerator:
    def __init__(self):
        self._seq = 0
        self._worker_id = os.getenv("WORKER_ID", 1)
        self._lock = threading.Lock()
        self._last_timestamp = -1

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def __call__(self) -> Snowflake:
        with self._lock:
            ts = self._timestamp()

            if ts == self._last_timestamp:
                self._seq = (self._seq + 1) & 0xFFF
            else:
                self._seq = 0

            self.last_timestamp = ts

            return Snowflake.from_data(ts, self._worker_id, self._seq)

generate_snowflake = _SnowflakeGenerator()

class Unique(abc.ABC):
    """Mixin for a class that enforces uniqueness by a snowflake ID."""

    __slots__: collections.abc.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def id(self) -> Snowflake:
        """ID of this entity."""

    @property
    def created_at(self) -> datetime.datetime:
        """When the object was created."""
        return self.id.created_at

    @typing.final
    def __index__(self) -> int:
        return int(self.id)

    @typing.final
    def __int__(self) -> int:
        return int(self.id)

    @typing.override
    def __hash__(self) -> int:
        return hash(self.id)

    @typing.override
    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and self.id == other.id


Snowflakeish = Snowflake | int
"""Type hint for a value that resembles a `Snowflake` object functionally.

This is a value that is `Snowflake`-ish.

A value is `Snowflake`-ish if casting it to an `int` allows it to be cast to
a `Snowflake`.

The valid types for this type hint are:

- `int`
- `Snowflake`
"""

T_co = typing.TypeVar("T_co", covariant=True, bound=Unique)

SnowflakeishOr = T_co | Snowflakeish
"""Type hint representing a unique object entity.

This is a value that is [`hikari.snowflakes.Snowflake`][]-ish or a specific type covariant.

If you see `SnowflakeishOr[Foo]` anywhere as a type hint, it means the value
may be a `Foo` instance, a [`hikari.snowflakes.Snowflake`][], an [`int`][] or a [`str`][]
with numeric digits only.

Essentially this represents any concrete object, or ID of that object. It is
used across Hikari's API to allow use of functions when information is only
partially available (due to Discord inconsistencies, edge case behaviour, or
use of intents).

The valid types for this type hint are:

- [`int`][]
- [`hikari.snowflakes.Snowflake`][]
"""