"""Entrypoint for our application."""

from __future__ import annotations

import sanic
from sanic.log import logger

from backend.models.responses import Success
from backend.models.responses import Test
from backend.serialization import deserialize
from backend.serialization import serialize

app = sanic.Sanic("Casino")


@app.post("/")
@serialize()
@deserialize()
async def hello_world(_: sanic.Request, body: Test) -> Success:
    """Hello World endpoint to test if the server is running."""
    logger.info(body.test)
    return Success()
