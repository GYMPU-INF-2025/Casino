from __future__ import annotations

import random
import typing

from backend.internal.ws import GameLobbyBase
from backend.internal.ws import WebsocketClient
from backend.internal.ws import add_event_listener
from shared.models import events

if typing.TYPE_CHECKING:
    from backend.db.queries import Queries


class Chickengame(GameLobbyBase):
    def __init__(self, *, lobby_id: str, queries: Queries) -> None:
        super().__init__(lobby_id=lobby_id, queries=queries)

        self.money = 1000
        self.stake = 0
        self.take = 0
        self.gamemode = 0
        self.step = 1

    @add_event_listener(events.UpdateMoney)
    async def update_money_callback(self, event: events.UpdateMoney, _: WebsocketClient) -> None:
        self.money = event.money
        await self.broadcast_event(events.UpdateMoney(money=self.money))

    @add_event_listener(events.UpdateGamemode)
    async def update_gamemode_callback(self, event: events.UpdateGamemode, _: WebsocketClient) -> None:
        self.gamemode = event.gamemode

    @add_event_listener(events.UpdateMultiplier)
    async def update_multiplier_callback(self, event: events.UpdateMultiplier, _: WebsocketClient) -> None:
        await self.broadcast_event(
            events.UpdateMultiplierResponse(multiplier=self.give_multiplier(event.step_text), step_text=event.step_text)
        )

    @add_event_listener(events.DoStep)
    async def do_step_callback(self, event: events.DoStep, _: WebsocketClient) -> None:
        self.stake = event.stake
        self.take = event.take
        self.step = event.step + 1
        rand = random.random()
        if rand < self.give_probability():
            self.take = self.stake * self.give_multiplier(self.step)
            await self.broadcast_event(events.DoStepResponse(take=int(self.take)))
        else:
            await self.broadcast_event(events.DoStepResponse(take=0))

    def give_probability(self) -> float:
        if self.gamemode == 0:
            return round((0.98 - (self.step - 1) * 0.01), 3)
        if self.gamemode == 1:
            return round((0.90 - (self.step - 1) * 0.01), 3)
        return round((0.80 - (self.step - 1) * 0.02), 3)

    def give_multiplier(self, step: int) -> float:
        if self.gamemode == 0:
            return round((1.01 * 1.01 ** (step - 1)), 3)
        if self.gamemode == 1:
            return round((1.02 * 1.015 ** (step - 1)), 3)
        return round((1.03 * 1.02 ** (step - 1)), 3)

    @add_event_listener(events.ReadyEvent)
    async def ready_callback(self, event: events.ReadyEvent, _: WebsocketClient) -> None:
        self.money = event.user.money
        await self.broadcast_event(events.UpdateMoney(money=self.money))

    @add_event_listener(events.UpdateTotal)
    async def update_total_callback(self, event: events.UpdateTotal, _: WebsocketClient) -> None:
        await self.queries.update_user_money(money=event.total, id_=_.user_id)

    @property
    @typing.override
    def max_num_clients(self) -> int:
        return 1

    @staticmethod
    @typing.override
    def endpoint() -> str:
        return "chickengame"
