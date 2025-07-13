from __future__ import annotations

import typing

import msgspec
from sanic.log import logger

from backend.internal import errors
from backend.utils import convert_struct
from shared.internal import Snowflake
from shared.internal import generate_snowflake
from shared.internal.hooks import encode_hook
from shared.internal.opcodes import DISPATCH
from shared.internal.opcodes import READY
from shared.models import events
from shared.models.internal import WebSocketPayload
from shared.models.responses import PublicUser

if typing.TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Coroutine

    import sanic

    from backend.db.models import User
    from backend.internal.ws.websocket_manager import _WebsocketTransport

__all__ = ("WebsocketClient",)


class WebsocketClient:
    def __init__(
        self, ws: _WebsocketTransport, request: sanic.Request, user_id: Snowflake, client_id: Snowflake
    ) -> None:
        self._ws = ws
        self._request = request
        self._user_id = user_id
        self._client_id = client_id

    @property
    def ws(self) -> _WebsocketTransport:
        return self._ws

    @property
    def client_id(self) -> Snowflake:
        return self._client_id

    @property
    def user_id(self) -> Snowflake:
        return self._user_id

    @classmethod
    def new_client(cls, ws: _WebsocketTransport, request: sanic.Request, user_id: Snowflake) -> WebsocketClient:
        return cls(ws=ws, request=request, user_id=user_id, client_id=generate_snowflake())

    async def dispatch_event(self, data: dict[str, typing.Any], event_name: str) -> None:
        await self._ws.send_payload(WebSocketPayload(op=DISPATCH, d=data, t=event_name))

    async def send_ready(self, user: User, num_clients: int) -> events.ReadyEvent:
        ready_event = events.ReadyEvent(
            user=convert_struct(user, PublicUser), client_id=self._client_id, num_clients=num_clients
        )
        await self._ws.send_payload(
            WebSocketPayload(op=READY, d=msgspec.to_builtins(ready_event, enc_hook=encode_hook))
        )
        return ready_event

    async def handle_ws(
        self,
        dispatch_handler: Callable[[WebSocketPayload, WebsocketClient], Coroutine[typing.Any, typing.Any, None]],
        remove_client: Callable[[Snowflake], Coroutine[typing.Any, typing.Any, None]],
    ) -> None:
        while True:
            try:
                payload = await self._ws.recieve_payload()
            except errors.WebsocketConnectionError as exc:
                logger.debug(f"Client {self.client_id} closed the connection with reason {exc.reason}")
                await remove_client(self._user_id)
                break
            except errors.WebsocketClientClosedConnectionError as exc:
                logger.debug(
                    f"Client {self.client_id} closed the connection with code {exc.code} and reason {exc.reason}"
                )
                await remove_client(self._user_id)
                break
            else:
                if payload.op == DISPATCH:
                    await dispatch_handler(payload, self)
