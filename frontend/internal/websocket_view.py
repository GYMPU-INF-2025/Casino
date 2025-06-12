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
    @typing.override
    def __call__(
        cls: type[WebsocketViewT], window: MainWindow, game_mode: c.GameModes, lobby_id: str
    ) -> WebsocketViewT:
        obj = super().__call__(window=window, game_mode=game_mode, lobby_id=lobby_id)
        obj.__post__init__()
        return obj


class WebsocketView(BaseGameView, metaclass=_WebsocketViewMeta):
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
        for attr_name in dir(self):
            maybe_listener = getattr(self, attr_name)

            if callable(maybe_listener) and hasattr(maybe_listener, "__event_type__"):
                self.add_event_callback(maybe_listener.__event_type__, maybe_listener)  # type: ignore[reportArgumentType]
        self.start()

    def __on_ws_disconnect(self) -> None:
        self._show_main_menu.set()

    def add_event_callback(
        self, event_type: type[events.BaseEvent], callback: collections.abc.Callable[[events.BaseEvent], None]
    ) -> None:
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
        self._ws_thread.start()

    def send_event(self, event: events.BaseEvent) -> None:
        event_name = event.event_name()
        data = msgspec.to_builtins(event, enc_hook=encode_hook)
        self._ws_thread.dispatch_event(data, event_name)

    @typing.override
    def on_update(self, delta_time: float) -> bool | None:
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

    def __del__(self) -> None:
        self._ws_thread.disconnect()
