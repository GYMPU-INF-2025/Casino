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
from backend.db.queries import Queries
from backend.internal.errors import InternalServerError
from backend.internal.serialization import deserialize
from backend.internal.serialization import serialize
from backend.internal.ws import GameLobbyBase
from backend.internal.ws import WebsocketClient
from backend.internal.ws import WebsocketEndpointsManager
from backend.internal.ws import add_event_listener
from backend import utils
from shared.internal.hooks import encode_hook
from shared.internal.snowflakes import Snowflake
from shared.models import ErrorResponse
from shared.models import events
from shared.models import PublicUser
from shared.models.responses import Success
from shared.models.responses import Test

if typing.TYPE_CHECKING:
    import asyncio


class Blackjack(GameLobbyBase):
    def __init__(self, *, lobby_id: str, queries: Queries) -> None:
        super().__init__(lobby_id=lobby_id, queries=queries)
        self.money = 0

    @add_event_listener(events.UpdateMoney)
    async def update_money_callback(self, event: events.UpdateMoney, _: WebsocketClient) -> None:
        self.money = event.money
        await self.broadcast_event(events.UpdateMoney(money=self.money))

    @property
    @typing.override
    def max_num_clients(self) -> int:
        return 2

    @staticmethod
    @typing.override
    def endpoint() -> str:
        return "blackjack"


PROJECT_DIR = pathlib.Path(__file__).parent.parent
DB_DIR = PROJECT_DIR / "db"

app = sanic.Sanic("Casino")
app.blueprint(auth_router)
queries_: Queries | None = None


@app.before_server_start
async def setup_db(app_: sanic.Sanic, _: asyncio.AbstractEventLoop) -> None:
    """Create database connection."""
    aiosqlite_conn = await aiosqlite.connect("sqlite.db")
    await aiosqlite_conn.executescript((DB_DIR / "schema.sql").read_text())
    global queries_
    queries_ = Queries(aiosqlite_conn)
    app_.ext.dependency(queries_)


@app.after_server_stop
async def teardown_db(__: sanic.Sanic, _: asyncio.AbstractEventLoop) -> None:
    """Close the database connection when server shutting down."""
    if queries_ is not None:
        await queries_.conn.close()


ws_endpoints = WebsocketEndpointsManager(app=app)
ws_endpoints.add_lobby(game_lobby_type=Blackjack)

error_encoder = msgspec.json.Encoder(enc_hook=encode_hook)


@app.all_exceptions
async def handler(_: sanic.Request, exception: Exception) -> sanic.HTTPResponse:
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


async def get_current_user(request: sanic.Request, queries: Queries) -> PublicUser:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise sanic.SanicException(
            message="Authorization header is missing.",
            status_code=http.HTTPStatus.UNAUTHORIZED
        )
    token = auth_header.split(" ")[-1]

    try:
        user_id = utils.decode_token(token)
        db_user = await queries.get_user_by_id(id_=user_id)
        return PublicUser(
            id=db_user.id,
            username=db_user.username,
            money=db_user.money
        )
    except Exception:
        raise sanic.SanicException(
            message="Invalid token",
            status_code=http.HTTPStatus.UNAUTHORIZED
        )


@app.get("/me")
@serialize()
@deserialize()
async def get_me(_: sanic.Request, queries: Queries) -> PublicUser:
    """
    Get the current user's information.
    """
    db_user = await get_current_user(_, queries)
    return db_user


@app.post("/")
@serialize()
@deserialize()
async def hello_world(_: sanic.Request, body: Test, query: Queries) -> Success:
    """Hello World endpoint to test if the server is running."""
    logger.info(body.test)
    user = await query.get_user_by_id(id_=Snowflake(20000))
    if user is None:
        return Success(message="User not found!")
    return Success(message=user.username)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
