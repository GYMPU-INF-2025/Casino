from __future__ import annotations

import asyncio
import typing

import jwt
import msgspec.json
import sanic
import websockets
from sanic.log import logger

from backend.internal import Snowflake
from backend.internal import errors
from backend.internal.ws import GameLobbyBase
from backend.internal.ws.opcodes import _HELLO
from backend.internal.ws.opcodes import _IDENTIFY
from backend.internal.ws.websocket_client import WebsocketClient
from backend.models import internal as models
from backend.utils import tokens

if typing.TYPE_CHECKING:
    from backend.db.queries import Queries

__all__ = ("WebsocketManager", "_WebsocketTransport")


class _WebsocketTransport:
    def __init__(self, *, ws: sanic.Websocket) -> None:
        self._ws = ws
        self._decoder = msgspec.json.Decoder(type=models.WebSocketPayload)
        self._encoder = msgspec.json.Encoder()
        self._sent_close = False

    async def send_close(self, *, code: int, reason: str) -> None:
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
        except websockets.ConnectionClosed as e:
            self._handle_close(e)
        except asyncio.CancelledError:
            msg = "Client has closed"
            raise errors.WebsocketConnectionError(reason=msg) from None
        except sanic.ServerError as exc:
            msg = "Internal Server Error"
            raise errors.WebsocketConnectionError(reason=msg) from exc
        else:
            if isinstance(data, str):
                return data.encode()
                # msg = "Unexpected message type received TEXT, expected BINARY"
                # raise errors.WebsocketTransportError(reason=msg)
            if data is None:
                msg = "Unexpected message received None, expected BINARY"
                raise errors.WebsocketTransportError(reason=msg)
            return data

    def _handle_close(self, close: websockets.ConnectionClosed) -> typing.NoReturn:
        logger.debug("handling close")
        if rcvd := close.rcvd:
            raise errors.WebsocketClientClosedConnectionError(reason=rcvd.reason, code=rcvd.code)
        msg = "Client has closed"
        raise errors.WebsocketConnectionError(reason=msg)


T = typing.TypeVar("T", bound=GameLobbyBase)


class WebsocketManager(typing.Generic[T]):
    def __init__(self, lobby_class: type[T]) -> None:
        self._lobby_class = lobby_class
        self._lobbys: dict[str, T] = {}
        self._identify_decoder = msgspec.json.Decoder(type=models.IdentifyPayload)

    async def handle_websocket(
        self, request: sanic.Request, ws: sanic.Websocket, lobby_id: str, queries: Queries
    ) -> None:
        _ws = _WebsocketTransport(ws=ws)
        if not (lobby := self._lobbys.get(lobby_id)):
            lobby = self._lobby_class(lobby_id=lobby_id)
            self._lobbys[lobby_id] = lobby
        try:
            user_id = await self._connect(ws=_ws, request=request, lobby=lobby, queries=queries)

        except OverflowError as exc:
            msg = f"client tried joining lobby {lobby_id} even though the lobby is full."
            logger.debug(msg, exc_info=exc)
            await _ws.send_close(code=errors.WebsocketCloseCode.LOBBY_FULL, reason="Lobby is full")

        except errors.WebsocketConnectionError as ex:
            logger.warning("failed to communicate with client, reason was: %r.", ex.reason)

        except errors.WebsocketTransportError as ex:
            logger.warning("encountered transport error, reason was: %r.", ex.reason)

        except errors.WebsocketClientClosedConnectionError as ex:
            logger.info("client has closed the connection. [code:%s, reason:%s]", ex.code, ex.reason)

        except errors.WebsocketError as exc:
            logger.exception("encountered gateway error", exc_info=exc)
            raise

        except Exception as exc:
            logger.exception("encountered some unhandled error", exc_info=exc)
            raise

        else:
            await lobby.handle_ws(user_id)

    async def _connect(
        self, *, ws: _WebsocketTransport, request: sanic.Request, lobby: T, queries: Queries
    ) -> Snowflake:
        await ws.send_payload(payload=models.WebSocketPayload(op=_HELLO, d={}))
        try:
            payload = await ws.recieve_payload()
            if payload.op == _IDENTIFY:
                ident_payload = msgspec.convert(payload.d, type=models.IdentifyPayload)
                user_id = tokens.decode_token(ident_payload.token)
                user = await queries.get_user_by_id(id_=user_id)
                if not user:
                    msg = (
                        f"token used for authentication contained id: {user_id} which does not belong to any user,"
                        "closing with AUTHENTICATION_FAILED"
                    )
                    logger.debug(msg)
                    await ws.send_close(code=errors.WebsocketCloseCode.AUTHENTICATION_FAILED, reason="Unknown user")
                    raise errors.WebsocketConnectionError(reason=msg) from None
                lobby.set_client(user_id, WebsocketClient.new_client(ws=ws, request=request, user_id=user_id))
                await lobby.send_ready(user)
                return user_id
            msg = f"expected {_IDENTIFY} (IDENTIFY) opcode, received {payload.op}, closing with NOT_AUTHENTICATED"
            logger.debug(msg)
            await ws.send_close(code=errors.WebsocketCloseCode.NOT_AUTHENTICATED, reason="Expected HELLO or RESUME op")
            raise errors.WebsocketConnectionError(reason=msg) from None
        except jwt.PyJWTError as exc:
            msg = "received invalid jwt token from client, closing with AUTHENTICATION_FAILED"
            logger.debug(msg, exc_info=exc)
            await ws.send_close(code=errors.WebsocketCloseCode.NOT_AUTHENTICATED, reason="Expected HELLO or RESUME op")
            raise errors.WebsocketConnectionError(reason=msg) from None
        except msgspec.DecodeError as exc:
            msg = "received malformed json from the client, closing with DECODE_ERROR"
            logger.debug(msg, exc_info=exc)
            await ws.send_close(code=errors.WebsocketCloseCode.DECODE_ERROR, reason="Malformed json sent")
            raise errors.WebsocketConnectionError(reason=msg) from None
