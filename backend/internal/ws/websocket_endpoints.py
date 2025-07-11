from __future__ import annotations

import typing

from backend.internal.ws.websocket_manager import WebsocketManager

if typing.TYPE_CHECKING:
    import sanic
    from sanic.models.handler_types import RouteHandler

    from backend.internal.ws import GameLobbyBase

__all__ = ("WebsocketEndpointsManager",)


class WebsocketEndpointsManager:
    def __init__(self, app: sanic.Sanic) -> None:
        self._app = app
        self._endpoints = []

    def add_lobby(self, game_lobby_type: type[GameLobbyBase]) -> None:
        endpoint = WebsocketManager[game_lobby_type](game_lobby_type)
        self._app.add_websocket_route(endpoint.handle_websocket, f"/{game_lobby_type.endpoint()}/<lobby_id:str>",
            name=game_lobby_type.endpoint() + 'websocket',)
        self._app.add_route(
            handler=typing.cast("RouteHandler", endpoint.list_lobbys),
            uri=f"/{game_lobby_type.endpoint()}/",
            methods=frozenset({"GET"}),
            name=game_lobby_type.endpoint() + 'list_lobby',
        )
        self._app.add_route(
            handler=typing.cast("RouteHandler", endpoint.create_lobby),
            uri=f"/{game_lobby_type.endpoint()}/",
            methods=frozenset({"POST"}),
            name=game_lobby_type.endpoint() + 'create_lobby',
        )
