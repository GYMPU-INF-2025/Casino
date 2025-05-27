"""Entrypoint for our application."""

from __future__ import annotations

import pathlib
import typing

import aiosqlite
import sanic
from sanic.log import logger

from backend.db.queries import Queries
from backend.internal.serialization import deserialize
from backend.internal.serialization import serialize
from backend.internal.snowflakes import Snowflake
from backend.internal.ws import GameLobbyBase
from backend.internal.ws import WebsocketClient
from backend.internal.ws import WebsocketEndpointsManager
from backend.models import events
from backend.models.responses import Success
from backend.models.responses import Test

if typing.TYPE_CHECKING:
    import asyncio


class LobbyImpl(GameLobbyBase):
    def __init__(self, lobby_id: str) -> None:
        super().__init__(lobby_id)
        self.add_event_callback(events.TestEvent, self.test_callback)

    async def test_callback(self, event: events.TestEvent, client: WebsocketClient) -> None:
        logger.info(event.money)
        logger.info(self.num_clients)
        logger.info(client.client_id)

    @property
    def max_num_clients(self) -> int:
        return 2

    @property
    def endpoint(self) -> str:
        return "test"


PROJECT_DIR = pathlib.Path(__file__).parent.parent
DB_DIR = PROJECT_DIR / "db"

app = sanic.Sanic("Casino")
queries: Queries | None = None


@app.before_server_start
async def setup_db(app_: sanic.Sanic, _: asyncio.AbstractEventLoop) -> None:
    """Create database connection."""
    aiosqlite_conn = await aiosqlite.connect("sqlite.db")
    await aiosqlite_conn.executescript((DB_DIR / "schema.sql").read_text())
    global queries
    queries = Queries(aiosqlite_conn)
    app_.ext.dependency(queries)


@app.after_server_stop
async def teardown_db(__: sanic.Sanic, _: asyncio.AbstractEventLoop) -> None:
    """Close the database connection when server shutting down."""
    if queries is not None:
        await queries.conn.close()


ws_endpoints = WebsocketEndpointsManager(app=app)
ws_endpoints.add_lobby(game_lobby_type=LobbyImpl)


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
