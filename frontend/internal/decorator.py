from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from collections.abc import Callable

    from frontend.internal import websocket_view
    from shared.models import events

    WebsocketViewT = typing.TypeVar("WebsocketViewT", bound=websocket_view.WebsocketView)
    EventT = typing.TypeVar("EventT", bound=events.BaseEvent)
    DecoratorCallbackT = Callable[[WebsocketViewT, EventT], None]


def add_event_listener(
    event: type[EventT],
) -> Callable[[DecoratorCallbackT[WebsocketViewT, EventT]], DecoratorCallbackT[WebsocketViewT, EventT]]:
    """Decorator used to mark a function as a callback for a certain event.

    Authors: Christopher
    """

    def wrapper(func: DecoratorCallbackT[WebsocketViewT, EventT]) -> DecoratorCallbackT[WebsocketViewT, EventT]:
        func.__event_type__ = event  # type: ignore[reportFunctionMemberAccess]
        return func

    return wrapper
