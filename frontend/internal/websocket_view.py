from __future__ import annotations

__all__ = ("WebsocketView",)

import abc
import inspect
import logging
import queue
import threading
import typing

import msgspec

from frontend.views.base import BaseGameView
from shared.internal.hooks import encode_hook

if typing.TYPE_CHECKING:
    import collections.abc

    from frontend import constants as c
    from frontend.window import MainWindow
    from shared.models import events


logger = logging.getLogger(__name__)


WebsocketViewT = typing.TypeVar("WebsocketViewT")


class _WebsocketViewMeta(abc.ABCMeta):
    """Metaclass for the websocket view to allow the `__post__init__` function to be called.

    Authors: Christopher
    """

    @typing.override
    def __call__(
        cls: type[WebsocketViewT], window: MainWindow, game_mode: c.GameModes, lobby_id: str
    ) -> WebsocketViewT:
        obj = super().__call__(window=window, game_mode=game_mode, lobby_id=lobby_id)
        obj.__post__init__()
        return obj


class WebsocketView(BaseGameView, metaclass=_WebsocketViewMeta):
    """Base class for game views that require a websocket connection to the server. The ws connection to the server
    is established after an instance of the class got created by using the provided game_mode and lobby id.

    It starts an WebsocketThread which listens for new websocket messages and pulls them out of the shared queue.
    This class also has a mapping for storing "event handlers". This mapping is populated after an instance of this
    class got created by looking for functions with an __event_type__ attribute. This is added when using the
    `add_event_listener` decorator. You can also use the `add_event_callback` function of this class to add new
    event handlers.

    Authors: Christopher
    """
    def __init__(self, window: MainWindow, game_mode: c.GameModes, lobby_id: str) -> None:
        super().__init__(window=window)
        self._game_mode = game_mode
        self._lobby_id = lobby_id
        self._receive_event_queue: queue.Queue[events.BaseEvent] = queue.Queue()
        self._send_event_queue: queue.Queue[events.BaseEvent] = queue.Queue()

        self._event_handlers: dict[str, list[collections.abc.Callable[[events.BaseEvent], None]]] = {}

        self._show_main_menu = threading.Event()
        self._ws_thread = window.net_client.get_websocket_thread(
            game_mode=game_mode,
            lobby_id=lobby_id,
            receive_event_queue=self._receive_event_queue,
            disconnect_callback=self.__on_ws_disconnect,
        )

    def __post__init__(self) -> None:
        """Function called after an instance of this class got created.

        This starts the websocket thread and looks for event listeners.
        """
        for attr_name in dir(self):
            maybe_listener = getattr(self, attr_name)

            if callable(maybe_listener) and hasattr(maybe_listener, "__event_type__"):
                self.add_event_callback(maybe_listener.__event_type__, maybe_listener)  # type: ignore[reportArgumentType]
        self.start()

    def __on_ws_disconnect(self) -> None:
        """Called when the websocket disconnects."""
        self._show_main_menu.set()

    def add_event_callback(
        self, event_type: type[events.BaseEvent], callback: collections.abc.Callable[[events.BaseEvent], None]
    ) -> None:
        """Function that adds an event handler/callback."""
        logger.debug(
            "subscribing callback 'async def %s%s' to event-type %s.%s",
            getattr(callback, "__name__", "<anon>"),
            inspect.signature(callback),
            event_type.__module__,
            event_type.__qualname__,
        )
        if event := self._event_handlers.get(event_type.event_name()):
            event.append(callback)
            self._event_handlers[event_type.event_name()] = event
        else:
            self._event_handlers[event_type.event_name()] = [callback]
        self._ws_thread.register_event(event_type)

    def start(self) -> None:
        """Function that starts the websocket thread."""
        self._ws_thread.start()

    def send_event(self, event: events.BaseEvent) -> None:
        """Helper function that sends an event to the websocket thread / server."""
        event_name = event.event_name()
        data = msgspec.to_builtins(event, enc_hook=encode_hook)
        self._ws_thread.dispatch_event(data, event_name)

    @typing.override
    def on_update(self, delta_time: float) -> bool | None:
        """This overrides the arcade `on_update` function. Every time this function gets called it looks for new
        events in the queue and pulls them out of the queue. It then dispatches them.
        """
        if self._show_main_menu.is_set():
            self.window.show_main_menu()
        else:

            def consume_event() -> None:
                try:
                    event = self._receive_event_queue.get_nowait()
                except queue.Empty:
                    return None
                logger.debug("Pulled event %s out of queue", event)
                if handlers := self._event_handlers.get(event.event_name()):
                    for handler in handlers:
                        try:
                            handler(event)
                        except Exception as exc:
                            logger.exception(
                                "Exception occurred when handling event %s", event.event_name(), exc_info=exc
                            )
                return consume_event()

            consume_event()

    @typing.override
    def deactivate(self) -> None:
        self._ws_thread.disconnect()

    def __del__(self) -> None:
        self._ws_thread.disconnect()
