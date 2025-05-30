from __future__ import annotations

import typing

import msgspec
from sanic.log import logger

from backend.internal import Snowflake
from backend.internal import errors
from backend.internal import generate_snowflake
from backend.internal.hooks import encode_hook
from backend.internal.ws.opcodes import _DISPATCH
from backend.internal.ws.opcodes import _READY
from backend.models.internal import ReadyPayload
from backend.models.internal import WebSocketPayload
from backend.models.responses import PublicUser
from backend.utils import convert_struct

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

    @classmethod
    def new_client(cls, ws: _WebsocketTransport, request: sanic.Request, user_id: Snowflake) -> WebsocketClient:
        return cls(ws=ws, request=request, user_id=user_id, client_id=generate_snowflake())

    async def dispatch_event(self, data: dict[str, typing.Any], event_name: str) -> None:
        await self._ws.send_payload(WebSocketPayload(op=_DISPATCH, d=data, t=event_name))

    async def send_ready(self, user: User, num_clients: int) -> None:
        await self._ws.send_payload(
            WebSocketPayload(
                op=_READY,
                d=msgspec.to_builtins(
                    ReadyPayload(
                        user=convert_struct(user, PublicUser), client_id=self._client_id, num_clients=num_clients
                    ),
                    enc_hook=encode_hook,
                ),
            )
        )

    async def handle_ws(
        self,
        dispatch_handler: Callable[[WebSocketPayload, WebsocketClient], Coroutine[typing.Any, typing.Any, None]],
        remove_client: Callable[[Snowflake], None],
    ) -> None:
        while True:
            try:
                payload = await self._ws.recieve_payload()
            except errors.WebsocketConnectionError as exc:
                logger.debug(f"Client {self.client_id} closed the connection with reason {exc.reason}")
                remove_client(self._user_id)
            except errors.WebsocketClientClosedConnectionError as exc:
                logger.debug(
                    f"Client {self.client_id} closed the connection with code {exc.code} and reason {exc.reason}"
                )
                remove_client(self._user_id)
            else:
                if payload.op == _DISPATCH:
                    await dispatch_handler(payload, self)
