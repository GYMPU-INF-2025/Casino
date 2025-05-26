"""Entrypoint for our application."""

from __future__ import annotations

import sanic
from sanic.log import logger

from backend.internal.serialization import deserialize
from backend.internal.serialization import serialize
from backend.models.responses import Success
from backend.models.responses import Test
from backend.internal.ws import WebsocketEndpointsManager, GameLobbyBase


class LobbyImpl(GameLobbyBase):

    @property
    def endpoint(self) -> str:
        return "test"


app = sanic.Sanic("Casino")

ws_endpoints = WebsocketEndpointsManager(app=app)
ws_endpoints.add_lobby(game_lobby_type=LobbyImpl)


@app.post("/")
@deserialize()
@serialize()
async def hello_world(_: sanic.Request, body: Test) -> Success:
    """Hello World endpoint to test if the server is running."""
    logger.info(body.test)
    return Success()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)