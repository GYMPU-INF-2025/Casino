from __future__ import annotations

__all__ = ("DisconnectCallbackT", "WebsocketThread")

import collections.abc
import logging
import threading
import typing

import msgspec
import websocket

from shared.internal import opcodes
from shared.internal.hooks import decode_hook
from shared.models import events
from shared.models import internal as internal_models

if typing.TYPE_CHECKING:
    import queue

    from frontend import constants as c

type DisconnectCallbackT = collections.abc.Callable[..., None]

logger = logging.getLogger(__name__)


class _WebsocketTransport:
    def __init__(self, *, ws: websocket.WebSocket) -> None:
        self._ws = ws
        self._decoder = msgspec.json.Decoder(type=internal_models.WebSocketPayload)
        self._encoder = msgspec.json.Encoder()
        self._sent_close = False

    @property
    def closed(self) -> bool:
        return self._sent_close

    def send_close(self, *, code: int, reason: str) -> None:
        if self._sent_close:
            return

        self._sent_close = True
        logger.debug("sending close frame with code %s and message %s", code, reason)
        self._ws.close(status=code, reason=reason.encode())

    def recieve_payload(self) -> internal_models.WebSocketPayload:
        json = self._recieve_data()

        logger.debug("received payload with size %s\n    %s", len(json), json)

        return self._decoder.decode(json)

    def send_payload(self, payload: internal_models.WebSocketPayload) -> None:
        json = self._encoder.encode(payload)
        logger.debug("sending payload with size %s\n    %s", len(json), json)

        self._ws.send(json)

    def _recieve_data(self) -> bytes:
        data = self._ws.recv()
        if isinstance(data, str):
            msg = "Unexpected message type received TEXT, expected BINARY"
            raise websocket.WebSocketProtocolException(msg)
        if data is None:
            msg = "Unexpected message received None, expected BINARY"
            raise websocket.WebSocketProtocolException(msg)
        return data

    def abnormal_shutdown(self) -> None:
        self._ws.abort()
        self._ws.shutdown()


class WebsocketThread(threading.Thread):
    def __init__(
        self,
        token: str,
        ws_uri: str,
        game_mode: c.GameModes,
        lobby_id: str,
        receive_event_queue: queue.Queue[events.BaseEvent],
        disconnect_callback: DisconnectCallbackT,
    ) -> None:
        super().__init__(daemon=True)
        self._token = token
        self._receive_event_queue = receive_event_queue
        self._game_mode = game_mode
        self._lobby_id = lobby_id
        self._ws_uri = ws_uri
        self._disconnect_callback = disconnect_callback

        self._event_maps: dict[str, type[events.BaseEvent]] = {}

        self._ws: _WebsocketTransport | None = None
        self._stop_event = threading.Event()

    def register_event(self, event_type: type[events.BaseEvent]) -> None:
        self._event_maps[event_type.event_name()] = event_type

    def dispatch_event(self, data: dict[str, typing.Any], event_name: str) -> None:
        if self._ws:
            self._ws.send_payload(internal_models.WebSocketPayload(op=opcodes.DISPATCH, d=data, t=event_name))

    def __handle_dispatch(self, payload: internal_models.WebSocketPayload) -> None:
        if payload.op == opcodes.READY:
            if (event := self._event_maps.get(events.ReadyEvent.event_name())) is None:
                return
        elif payload.t is not None:
            if (event := self._event_maps.get(payload.t)) is None:
                return
        else:
            return

        event_obj = msgspec.convert(payload.d, type=event, dec_hook=decode_hook)
        self._receive_event_queue.put(event_obj)

    @typing.override
    def run(self) -> None:
        ws_endpoint = f"{self._ws_uri}{self._game_mode.value}/{self._lobby_id}/"
        try:
            ws = websocket.create_connection(ws_endpoint)
        except websocket.WebSocketException as exc:
            logger.exception(
                "Error while connecting to the websocket server with endpoint %s.", ws_endpoint, exc_info=exc
            )
            self._disconnect_callback()
            return

        self._ws = _WebsocketTransport(ws=ws)
        logger.debug("Established websocket connection with server using endpoint %s. Waiting for hello.", ws_endpoint)
        try:
            payload = self._ws.recieve_payload()
            if payload.op != opcodes.HELLO:
                logger.error(
                    "Expected opcode %s (HELLO), but received %s. Closing connection.", opcodes.HELLO, payload.op
                )
                self._ws.send_close(code=websocket.STATUS_ABNORMAL_CLOSED, reason="Expected HELLO opcode.")
                self._disconnect_callback()
                return
            logger.debug("Received HELLO opcode, sending IDENTIFY.")
            self._ws.send_payload(internal_models.WebSocketPayload(op=opcodes.IDENTIFY, d={"token": self._token}))
            payload = self._ws.recieve_payload()
            if payload.op != opcodes.READY:
                logger.error(
                    "Expected opcode %s (READY), but received %s. Closing connection.", opcodes.READY, payload.op
                )
                self._ws.send_close(code=websocket.STATUS_ABNORMAL_CLOSED, reason="Expected READY opcode.")
                self._disconnect_callback()
                return
            logger.debug("Received READY opcode.")
            self.__handle_dispatch(payload)
        except websocket.WebSocketException as exc:
            logger.exception("Exception occurred while identifying with the server.", exc_info=exc)
            self.abnormal_shutdown()
        except ConnectionResetError as exc:
            logger.debug(str(exc))
            self._stop_event.set()
        try:
            while not self._stop_event.set():
                payload = self._ws.recieve_payload()
                if payload.op == opcodes.DISPATCH:
                    self.__handle_dispatch(payload)
                else:
                    logger.warning("Unexpected opcode %s received in payload.", payload.op)
        except websocket.WebSocketException:
            logger.debug("Exception while receiving data, closing connection.")
            self.abnormal_shutdown()
        except ConnectionResetError as exc:
            logger.debug(str(exc))
        self._disconnect_callback()

    def abnormal_shutdown(self) -> None:
        self._stop_event.set()
        if self._ws is not None:
            self._ws.abnormal_shutdown()

    def disconnect(self) -> None:
        self._stop_event.set()
        if self._ws:
            self._ws.send_close(code=websocket.STATUS_NORMAL, reason="Client disconnected.")
