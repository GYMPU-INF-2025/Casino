from __future__ import annotations

import asyncio
import random
import string
import typing

import jwt
import msgspec.json
import sanic
import websockets
from sanic.log import logger

from backend.db import models as db_models  # noqa: TC001
from backend.db.queries import Queries  # noqa: TC001
from backend.internal import errors
from backend.internal import serialization
from backend.internal.ws import GameLobbyBase
from backend.internal.ws.websocket_client import WebsocketClient
from backend.utils import tokens
from shared.internal import opcodes
from shared.models import internal as internal_models
from shared.models import responses

if typing.TYPE_CHECKING:
    from shared.internal import Snowflake

__all__ = ("WebsocketManager", "_WebsocketTransport")


class _WebsocketTransport:
    def __init__(self, *, ws: sanic.Websocket) -> None:
        self._ws = ws
        self._decoder = msgspec.json.Decoder(type=internal_models.WebSocketPayload)
        self._encoder = msgspec.json.Encoder()
        self._sent_close = False

    async def send_close(self, *, code: int, reason: str) -> None:
        if self._sent_close:
            return

        self._sent_close = True
        logger.debug("sending close frame with code %s and message %s", code, reason)
        await self._ws.close(code=code, reason=reason)

    async def recieve_payload(self) -> internal_models.WebSocketPayload:
        json = await self._recieve_data()

        logger.debug("received payload with size %s\n    %s", len(json), json)

        return self._decoder.decode(json)

    async def send_payload(self, payload: internal_models.WebSocketPayload) -> None:
        json = self._encoder.encode(payload)
        logger.debug("sending payload with size %s\n    %s", len(json), json)

        await self._ws.send(json)

    async def _recieve_data(self) -> bytes:
        try:
            data = await self._ws.recv()
        except websockets.ConnectionClosed as e:
            self._handle_close(e)
        except asyncio.CancelledError:
            msg = "Client cancelled"
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
        if rcvd := close.rcvd:
            raise errors.WebsocketClientClosedConnectionError(reason=rcvd.reason, code=rcvd.code)
        msg = "Client has closed"
        raise errors.WebsocketConnectionError(reason=msg)


T = typing.TypeVar("T", bound=GameLobbyBase)


class WebsocketManager(typing.Generic[T]):
    def __init__(self, lobby_class: type[T]) -> None:
        self._lobby_class = lobby_class
        self._lobbys: dict[str, T] = {}
        self._identify_decoder = msgspec.json.Decoder(type=internal_models.IdentifyPayload)

    async def handle_websocket(
        self, request: sanic.Request, ws: sanic.Websocket, lobby_id: str, queries: Queries
    ) -> None:
        _ws = _WebsocketTransport(ws=ws)
        if not (lobby := self._lobbys.get(lobby_id)):
            msg = f"client tried joining lobby using invalid lobby id {lobby_id}."
            logger.debug(msg)
            await _ws.send_close(code=errors.WebsocketCloseCode.INVALID_LOBBY, reason="Lobby not found")
            return
        try:
            user_id = await self._connect(ws=_ws, request=request, lobby=lobby, queries=queries)

        except OverflowError:
            msg = f"client tried joining lobby {lobby_id} even though the lobby is full."
            logger.debug(msg)
            await _ws.send_close(code=errors.WebsocketCloseCode.LOBBY_FULL, reason="Lobby is full")

        except errors.WebsocketConnectionError as ex:
            logger.warning("failed to communicate with client, reason was: %r.", ex.reason)

        except errors.WebsocketTransportError as ex:
            logger.warning("encountered transport error, reason was: %r.", ex.reason)

        except errors.WebsocketClientClosedConnectionError as ex:
            logger.info("client has closed the connection. [code:%s, reason:%s]", ex.code, ex.reason)

        except errors.WebsocketError as exc:
            logger.exception("encountered gateway error", exc_info=exc)

        except Exception as exc:  # noqa: BLE001
            logger.exception("encountered some unhandled error", exc_info=exc)

        else:
            await lobby.handle_ws(user_id)

    async def _connect(
        self, *, ws: _WebsocketTransport, request: sanic.Request, lobby: T, queries: Queries
    ) -> Snowflake:
        await ws.send_payload(payload=internal_models.WebSocketPayload(op=opcodes.HELLO, d={}))
        try:
            payload = await ws.recieve_payload()
            if payload.op == opcodes.IDENTIFY:
                ident_payload = msgspec.convert(payload.d, type=internal_models.IdentifyPayload)
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
            msg = (
                f"expected {opcodes.IDENTIFY} (IDENTIFY) opcode, received {payload.op}, closing with NOT_AUTHENTICATED"
            )
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

    @serialization.serialize()
    async def list_lobbys(self, _: sanic.Request) -> list[responses.PublicGameLobby]:
        return [
            responses.PublicGameLobby(
                max_clients=lobby.max_num_clients, id=l_id, num_clients=lobby.num_clients, full=lobby.is_full
            )
            for l_id, lobby in self._lobbys.items()
        ]

    def _gen_new_lobby_id(self) -> str:
        chars = string.ascii_uppercase + string.digits
        while True:
            lobby_id = "".join(random.choices(chars, k=5))
            if not self._lobbys.get(lobby_id):
                return lobby_id

    @serialization.serialize()
    async def create_lobby(self, _: sanic.Request, queries: Queries, user: db_models.User) -> responses.PublicGameLobby:
        lobby_id = self._gen_new_lobby_id()
        logger.debug("user %s requested creating lobby %s", user.id, lobby_id)
        lobby = self._lobby_class(lobby_id=lobby_id, queries=queries)
        self._lobbys[lobby_id] = lobby
        return responses.PublicGameLobby(
            max_clients=lobby.max_num_clients, id=lobby_id, num_clients=lobby.num_clients, full=lobby.is_full
        )
