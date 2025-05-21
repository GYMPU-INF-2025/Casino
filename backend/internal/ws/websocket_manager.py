import asyncio
import typing

import msgspec.json
import sanic
import websockets

from backend.internal.ws import GameLobbyBase
from backend.internal import errors
from sanic.log import logger
from backend.models import internal as models

_HELLO: typing.Final[int] = 1
_IDENTIFY: typing.Final[int] = 2
_RESUME: typing.Final[int] = 3

class _WebsocketTransport:

    def __init__(self, *, ws: sanic.Websocket):
        self._ws = ws
        self._decoder = msgspec.json.Decoder(type=models.WebSocketPayload)
        self._encoder = msgspec.json.Encoder()
        self._sent_close = False

    async def send_close(self, *, code: int, reason: str):
        if self._sent_close:
            return

        self._sent_close = True
        logger.debug("sending close frame with code %s and message %s", code, reason)
        await self._ws.close(code=code, reason=reason)

    async def recieve_payload(self) -> models.WebSocketPayload:
        json = await self._recieve_data()

        logger.debug("received payload with size %s\n    %s", len(json), json)

        return self._decoder.decode(json)

    async def send_payload(self, payload: models.WebSocketPayload) -> None:
        json = self._encoder.encode(payload)
        logger.debug("sending payload with size %s\n    %s", len(json), json)

        await self._ws.send(json)


    async def _recieve_data(self) -> bytes:
        try:
            data = await self._ws.recv()
            if isinstance(data, str):
                return data.encode()
                #msg = "Unexpected message type received TEXT, expected BINARY"
                #raise errors.WebsocketTransportError(reason=msg)
            if data is None:
                msg = "Unexpected message received None, expected BINARY"
                raise errors.WebsocketTransportError(reason=msg)
            return data
        except websockets.ConnectionClosed as e:
            self._handle_close(e)
        except asyncio.CancelledError:
            msg = "Client has closed"
            raise errors.WebsocketConnectionError(reason=msg)
        except sanic.ServerError:
            msg = "Internal Server Error"
            raise errors.WebsocketConnectionError(reason=msg)

    def _handle_close(self, close: websockets.ConnectionClosed) -> typing.NoReturn:
        if rcvd := close.rcvd:
            raise errors.WebsocketClientClosedConnectionError(reason=rcvd.reason, code=rcvd.code)
        else:
            msg = "Client has closed"
            raise errors.WebsocketConnectionError(reason=msg)


class WebsocketClient:
    pass


class WebsocketManager:

    def __init__(self, game_lobby_type: type[GameLobbyBase]):
        self._game_lobby_type = game_lobby_type
        self._clients = []
        self._lobbys: dict[str, GameLobbyBase] = {}


    async def handle_websocket(self, request: sanic.Request, ws: sanic.Websocket, lobby_id: str) -> None:
        _ws = _WebsocketTransport(ws=ws)
        try:
            await self._connect(ws=_ws)

        except errors.WebsocketConnectionError as ex:
            logger.warning("failed to communicate with client, reason was: %r.", ex.reason)

        except errors.WebsocketTransportError as ex:
            logger.warning("encountered transport error, reason was: %r.", ex.reason)

        except errors.WebsocketClientClosedConnectionError as ex:
            logger.info("client has closed the connection. [code:%s, reason:%s]",ex.code, ex.reason)

        except errors.WebsocketError as exc:
            logger.exception("encountered gateway error", exc_info=exc)
            raise exc

        except Exception as exc:
            logger.exception("encountered some unhandled error", exc_info=exc)
            raise exc


    async def _connect(self, *, ws: _WebsocketTransport):
        await ws.send_payload(payload=models.WebSocketPayload(op=_HELLO, d={}))

        payload = await ws.recieve_payload()
        if payload.op == _IDENTIFY:
            pass
        elif payload.op == _RESUME:
            pass
        else:
            logger.debug(
                "expected %s (HELLO) or %s (RESUME) opcode, received %s which makes no sense, closing with PROTOCOL ERROR", _HELLO, _IDENTIFY, payload.op
            )
            await ws.send_close(code=errors.WebsocketCloseCode.NOT_AUTHENTICATED, reason="Expected HELLO or RESUME op")
            msg = f"Expected opcode {_HELLO} (HELLO) or {_RESUME} (RESUME), but received {payload.op}"
            raise errors.WebsocketError(reason=msg)
# Added `id` to reserved keywords so that it will appear as `id_`

