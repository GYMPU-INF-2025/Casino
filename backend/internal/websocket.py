"""Module containing logic to handle websocket connections."""

from __future__ import annotations

import typing

from sanic.log import logger

if typing.TYPE_CHECKING:
    import sanic
    import websockets


class WebsocketClient:
    """Websocket Client helper class."""

    def __init__(self, ws: sanic.Websocket, request: sanic.Request) -> None:
        """Initialize a WebsocketClient."""
        self._ws = ws
        self._request = request

    async def send(self, data: websockets.Data) -> None:
        """Send data to a client."""
        await self._ws.send(data)


class WebsocketManager:
    """Class that handles websocket connections and the clients."""

    def __init__(self, app: sanic.Sanic) -> None:
        """Initialize the WebsocketManager."""
        self._app = app
        self._app.add_websocket_route(self.__handle_websocket, "/ws")

        self._clients: list[WebsocketClient] = []

    async def broadcast(self, data: websockets.Data) -> None:
        """Send data to every connected client."""
        for client in self._clients:
            await client.send(data)

    async def __handle_websocket(self, request: sanic.Request, ws: sanic.Websocket) -> None:
        client = WebsocketClient(ws, request)
        self._clients.append(client)
        while True:
            data = await ws.recv()
            if data is not None:
                await self.broadcast(data)
            logger.info(data)
