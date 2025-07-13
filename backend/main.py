"""Entrypoint for our application."""

from __future__ import annotations

import http
import pathlib
import random
import typing

import aiosqlite
import msgspec.json
import sanic
from sanic.log import logger

from backend.authentication import router as auth_router
from backend.blackjack import Blackjack
from backend.db import models
from backend.db.queries import Queries
from backend.dependencys import get_current_user
from backend.internal.errors import InternalServerError
from backend.internal.serialization import deserialize
from backend.internal.serialization import serialize
from backend.internal.ws import WebsocketEndpointsManager
from backend.mines import Mines
from backend.users import router as users_router
from shared.internal.hooks import encode_hook
from shared.internal.snowflakes import Snowflake
from shared.models import ErrorResponse
from shared.models import events
from shared.models.events import Spin_Animation
from shared.models.responses import Success
from shared.models.responses import Test

if typing.TYPE_CHECKING:
    import asyncio


SlotSymbols = ["🍒", "🍋", "🔔", "💎", "⭐", "7️⃣"]
Prizes = {
    "🍒" : 10,
    "🍋" : 20,
    "🔔" : 50,
    "💎" : 100,
    "⭐" : 200,
    "7️⃣" : 500,
}

''' SYMBOL_MAP = {
    "a": "🍒",  # Kirsche
    "b": "🍋",  # Zitrone
    "c": "🔔",  # Glocke
    "d": "💎",  # Diamant
    "e": "⭐",  # Stern
    "f": "7️⃣", # Glückszahl 7
}
'''

class slot(GameLobbyBase):

    def __init__(self, *, lobby_id: str, queries: Queries) -> None:
        super().__init__(lobby_id=lobby_id, queries=queries)

        self.money = 30
        self.spin_cost = 5

    @add_event_listener(events.Moneyq)
    def Moneyq(self):
        self.send_event(events.Money_now(self.money))

    @add_event_listener(events.StartSpin)
    async def on_spin(self, event: events.StartSpin, _: WebsocketClient):
        if self.money < self.spin_cost:
            await self.broadcast_event(events.kein_Geld(self.spin_cost))
            return

        self.money = self.money - self.spin_cost
        outcome = [random.choice(SlotSymbols) for _ in range(3)]
        await self.broadcast_event(Spin_Animation(final_symbols=outcome))

        win = 0

        if outcome[0] == outcome[1] == outcome[2]:
            win = Prizes.get(outcome[0], 0)
        elif outcome[0] == outcome[1] or outcome[1] == outcome[2] or outcome[0] == outcome[2]:
            win = 2
            self.money += win
            self.broadcast_event(events.Slots_Win(self.money))
            return outcome, win, None

    @property
    @typing.override
    def max_num_clients(self) -> int:
        return 1

    @staticmethod
    @typing.override
    def endpoint() -> str:
        return "slots"

PROJECT_DIR = pathlib.Path(__file__).parent.parent
DB_DIR = PROJECT_DIR / "db"

app = sanic.Sanic("Casino")
app.blueprint(auth_router)
app.blueprint(users_router, url_prefix="/users")
queries_: Queries | None = None


@app.before_server_start
async def add_dependency(app_: sanic.Sanic, _: asyncio.AbstractEventLoop) -> None:
    """Create database connection."""
    aiosqlite_conn = await aiosqlite.connect("sqlite.db")
    await aiosqlite_conn.executescript((DB_DIR / "schema.sql").read_text())
    global queries_
    queries_ = Queries(aiosqlite_conn)
    app_.ext.dependency(queries_)
    app_.ext.add_dependency(models.User, get_current_user)


@app.after_server_stop
async def teardown_db(__: sanic.Sanic, _: asyncio.AbstractEventLoop) -> None:
    """Close the database connection when server shutting down."""
    if queries_ is not None:
        await queries_.conn.close()


ws_endpoints = WebsocketEndpointsManager(app=app)
ws_endpoints.add_lobby(game_lobby_type=Blackjack)
ws_endpoints.add_lobby(game_lobby_type=slot)
ws_endpoints.add_lobby(game_lobby_type=Mines)

error_encoder = msgspec.json.Encoder(enc_hook=encode_hook)


@app.all_exceptions
async def error_handler(_: sanic.Request, exception: Exception) -> sanic.HTTPResponse:
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
