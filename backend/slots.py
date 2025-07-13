from __future__ import annotations

import random
import typing

from backend.internal.ws import GameLobbyBase
from backend.internal.ws import WebsocketClient
from backend.internal.ws import add_event_listener
from shared.models import events
from shared.models.events import Spin_Animation

if typing.TYPE_CHECKING:
    from backend.db.queries import Queries

SlotSymbols = ["🍒", "🍋", "🔔", "💎", "⭐", "7️⃣"]
Prizes = {"🍒": 10, "🍋": 20, "🔔": 50, "💎": 100, "⭐": 200, "7️⃣": 500}


""" SYMBOL_MAP = {
    "a": "🍒",  # Kirsche
    "b": "🍋",  # Zitrone
    "c": "🔔",  # Glocke
    "d": "💎",  # Diamant
    "e": "⭐",  # Stern
    "f": "7️⃣", # Glückszahl 7
}
"""


class Slots(GameLobbyBase):
    def __init__(self, *, lobby_id: str, queries: Queries) -> None:
        super().__init__(lobby_id=lobby_id, queries=queries)

        self.money = 30
        self.spin_cost = 5

    @add_event_listener(events.Moneyq)
    async def moneyq(self, _: events.Moneyq, _ws: WebsocketClient) -> None:
        await self.send_event(events.Money_now(self.money), _ws)

    @add_event_listener(events.StartSpin)
    async def on_spin(self, _: events.StartSpin, __: WebsocketClient) -> None:
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
        await self.broadcast_event(events.Slots_Win(self.money))

    @property
    @typing.override
    def max_num_clients(self) -> int:
        return 1

    @staticmethod
    @typing.override
    def endpoint() -> str:
        return "slots"
