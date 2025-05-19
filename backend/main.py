"""Entrypoint for our application."""

from __future__ import annotations

import sanic
from sanic.log import logger

from backend.internal.serialization import deserialize
from backend.internal.serialization import serialize
from backend.internal.websocket import WebsocketManager
from backend.models.responses import Success
from backend.models.responses import Test

app = sanic.Sanic("Casino")
WebsocketManager(app)


@app.post("/")
@serialize()
@deserialize()
async def hello_world(_: sanic.Request, body: Test) -> Success:
    """Hello World endpoint to test if the server is running."""
    logger.info(body.test)
    return Success()
