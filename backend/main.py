"""Entrypoint for our application."""

from __future__ import annotations

import http
import pathlib
import typing

import aiosqlite
import msgspec.json
import sanic
from sanic.log import logger

from backend.authentication import router as auth_router
from backend.blackjack import Blackjack
from backend.chickengame import Chickengame
from backend.db import models
from backend.db.queries import Queries
from backend.dependencys import get_current_user
from backend.internal.errors import InternalServerError
from backend.internal.ws import WebsocketEndpointsManager
from backend.mines import Mines
from backend.slots import Slots
from backend.users import router as users_router
from shared.internal.hooks import encode_hook
from shared.models import ErrorResponse

if typing.TYPE_CHECKING:
    import asyncio


PROJECT_DIR = pathlib.Path(__file__).parent.parent
DB_DIR = PROJECT_DIR / "db"

app = sanic.Sanic("Casino")
app.blueprint(auth_router)
app.blueprint(users_router, url_prefix="/users")
queries_: Queries | None = None


@app.before_server_start
async def add_dependency(app_: sanic.Sanic, _: asyncio.AbstractEventLoop) -> None:
    """Create database connection.

    Authors: Christopher
    """
    aiosqlite_conn = await aiosqlite.connect("sqlite.db")
    await aiosqlite_conn.executescript((DB_DIR / "schema.sql").read_text())
    global queries_
    queries_ = Queries(aiosqlite_conn)
    app_.ext.dependency(queries_)
    app_.ext.add_dependency(models.User, get_current_user)


@app.after_server_stop
async def teardown_db(__: sanic.Sanic, _: asyncio.AbstractEventLoop) -> None:
    """Close the database connection when server shutting down.

    Authors: Christopher
    """
    if queries_ is not None:
        await queries_.conn.close()


ws_endpoints = WebsocketEndpointsManager(app=app)
ws_endpoints.add_lobby(game_lobby_type=Blackjack)
ws_endpoints.add_lobby(game_lobby_type=Chickengame)
ws_endpoints.add_lobby(game_lobby_type=Slots)
ws_endpoints.add_lobby(game_lobby_type=Mines)

error_encoder = msgspec.json.Encoder(enc_hook=encode_hook)


@app.all_exceptions
async def error_handler(_: sanic.Request, exception: Exception) -> sanic.HTTPResponse:
    """Error handler that returns a `ErrorResponse` as json for any error that occurs.

    Authors: Christopher
    """
    name: str = ""
    message: str = ""
    detail: str = ""
    if isinstance(exception, sanic.SanicException):
        try:
            code = http.HTTPStatus(exception.status_code)
            name = code.name
            message = code.phrase
            detail = code.description
        except ValueError:
            code = exception.status_code
        if exc_detail := exception.message:
            detail = exc_detail
        logger.debug("Handled Exception %s", exception)
    else:
        code = http.HTTPStatus(InternalServerError.status_code)
        name = code.name
        message = code.phrase
        detail = InternalServerError.message
        logger.exception("Unhandled Exception occurred", exc_info=exception)

    return sanic.raw(
        body=error_encoder.encode(ErrorResponse(message=message, detail=detail, name=name)),
        status=code,
        content_type="application/json",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
