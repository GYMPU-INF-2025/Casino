import sanic

from . import GameLobbyBase, WebsocketManager


class WebsocketEndpointsManager:

    def __init__(self, app: sanic.Sanic) -> None:
        self._app = app
        self._endpoints = []

    def add_lobby(self, game_lobby_type: type[GameLobbyBase]):
        endpoint = WebsocketManager(game_lobby_type)
        self._app.add_websocket_route(endpoint.handle_websocket, f"/test/<lobby_id:str>")



