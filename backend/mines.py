import logging
import typing
from backend.db.queries import Queries
from backend.internal.ws import GameLobbyBase
from backend.internal.ws import WebsocketClient
from backend.internal.ws import add_event_listener
from shared.models import events
import random


class Mines(GameLobbyBase):
    def __init__(self, *, lobby_id: str, queries: Queries) -> None:
        super().__init__(lobby_id=lobby_id, queries=queries)
        self.money = 1000
        self.stake = 0
        self.remaining_mines = 25
        self.num_mines = 4
        self.multiplier = 1.0

    @add_event_listener(events.UpdateMoney)
    async def update_money_callback(self, event: events.UpdateMoney, _: WebsocketClient) -> None:
        self.money = event.money
        await self.broadcast_event(events.UpdateMoney(money=self.money))

    @add_event_listener(events.ChangeStake)
    async def change_stake_callback(self, event: events.ChangeStake, _: WebsocketClient) -> None:
        self.stake += event.amount

    @add_event_listener(events.MineClicked)
    async def mine_clicked_callback(self, event: events.MineClicked, _: WebsocketClient) -> None:
        rand = random.randint(0, self.remaining_mines)
        if rand < self.num_mines:
            # Mine is clicked
            await self.broadcast_event(events.GameOver(x=event.x, y=event.y))
            return


        self.remaining_mines -= 1
        self.multiplier += 0.1
        await self.broadcast_event(events.MineClickedResponse(x=event.x, y=event.y, multiplier=self.multiplier))



    @property
    @typing.override
    def max_num_clients(self) -> int:
        return 1

    @staticmethod
    @typing.override
    def endpoint() -> str:
        return "mines"
