from __future__ import annotations

__all__ = ("NetClient",)

import typing

from frontend.internal import websocket_thread as ws_thread
from frontend.internal.rest_client import RestClientBase

if typing.TYPE_CHECKING:
    import queue

    from frontend import constants as c
    from shared.models import events


RestClientT = typing.TypeVar("RestClientT", bound=RestClientBase)


class NetClient(typing.Generic[RestClientT]):
    """The net client is a network client which is designed to handle all of our network communication.

    It stores our rest client and also handles websocket connections by providing a helper method that returns
    the thread needed for the websocket connection.

    This class also manages authorization by storing the jwt token used for auth and providing a login method.

    Authors: Christopher
    """
    def __init__(self, rest_client: type[RestClientT], base_address: str) -> None:
        self._rest_client: RestClientT = rest_client(base_url=f"http://{base_address}/")
        self._token: str | None = None
        self._ws_uri = f"ws://{base_address}/"

    @property
    def authorized(self) -> bool:
        return self._token is not None

    def set_token(self, token: str | None) -> None:
        self._token = token
        self._rest_client.set_token(token=token)

    def logout(self) -> None:
        self._token = None

    def login(self, username: str, password: str) -> None:
        response = self._rest_client.login(username=username, password=password)
        self.set_token(token=response.token)

    @property
    def rest(self) -> RestClientT:
        return self._rest_client

    def get_websocket_thread(
        self,
        game_mode: c.GameModes,
        lobby_id: str,
        receive_event_queue: queue.Queue[events.BaseEvent],
        disconnect_callback: ws_thread.DisconnectCallbackT,
    ) -> ws_thread.WebsocketThread:
        if self._token is None:
            raise ValueError("Client not authenticated.")
        return ws_thread.WebsocketThread(
            token=self._token,
            ws_uri=self._ws_uri,
            game_mode=game_mode,
            lobby_id=lobby_id,
            receive_event_queue=receive_event_queue,
            disconnect_callback=disconnect_callback,
        )
