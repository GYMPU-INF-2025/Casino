from __future__ import annotations

import typing

from backend.internal.ws import GameLobbyBase
from backend.internal.ws import WebsocketManager

if typing.TYPE_CHECKING:
    import sanic

__all__ = ("WebsocketEndpointsManager",)


class WebsocketEndpointsManager:
    def __init__(self, app: sanic.Sanic) -> None:
        self._app = app
        self._endpoints = []

    def add_lobby(self, game_lobby_type: type[GameLobbyBase]) -> None:
        endpoint = WebsocketManager[game_lobby_type](game_lobby_type)
        self._app.add_websocket_route(endpoint.handle_websocket, "/test/<lobby_id:str>")
