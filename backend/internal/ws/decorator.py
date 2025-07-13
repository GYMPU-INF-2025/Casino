from __future__ import annotations

__all__ = ("add_event_listener",)

import typing

if typing.TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Coroutine

    from backend.internal.ws import EventT
    from backend.internal.ws import GameLobbyBase
    from backend.internal.ws import WebsocketClient

    GameLobbyT = typing.TypeVar("GameLobbyT", bound=GameLobbyBase)
    DecoratorCallbackT = Callable[[GameLobbyT, EventT, WebsocketClient], Coroutine[typing.Any, typing.Any, None]]


def add_event_listener(
    event: type[EventT],
) -> Callable[[DecoratorCallbackT[GameLobbyT, EventT]], DecoratorCallbackT[GameLobbyT, EventT]]:
    """Decorator used to mark a function as a callback for a certain event.

    Authors: Christopher
    """

    def wrapper(func: DecoratorCallbackT[GameLobbyT, EventT]) -> DecoratorCallbackT[GameLobbyT, EventT]:
        func.__event_type__ = event  # type: ignore[reportFunctionMemberAccess]
        return func

    return wrapper
