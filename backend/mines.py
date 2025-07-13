import logging
import typing
from backend.db.queries import Queries
from backend.internal.ws import GameLobbyBase
from backend.internal.ws import WebsocketClient
from backend.internal.ws import add_event_listener
from shared.models import events
import random


class Mines(GameLobbyBase):
    '''
    Backend implementation of the Mines game.
    This class handles the game logic, including starting the game, handling mine clicks,
    calculating multipliers, and managing the player's money and stakes.

    Author: Quirin
    '''

    def __init__(self, *, lobby_id: str, queries: Queries) -> None:
        super().__init__(lobby_id=lobby_id, queries=queries)
        self.money = 1000
        self.stake = 0
        self.remaining_mines = 25
        self.num_mines = 4
        self.multiplier = self.calculate_multiplier()

    def calculate_multiplier(self) -> float:
        prob_safe_sequence = 1.0
        for i in range(25-self.remaining_mines):
            safe_left = 25 - self.num_mines - i
            tiles_left = 25 - i
            prob_safe_sequence *= safe_left / tiles_left

        return 1.0 / prob_safe_sequence

    @add_event_listener(events.ReadyEvent)
    async def start_game(self, event: events.ReadyEvent, _: WebsocketClient) -> None:
        self.money = event.user.money
        await self.send_event(events.UpdateMoney(money=self.money), _)


    @add_event_listener(events.ChangeStake)
    async def change_stake_callback(self, event: events.ChangeStake, _: WebsocketClient) -> None:
        self.stake += event.amount
        self.money -= event.amount

    @add_event_listener(events.MineClicked)
    async def mine_clicked_callback(self, event: events.MineClicked, _: WebsocketClient) -> None:
        rand = random.randint(0, self.remaining_mines)
        if rand < self.num_mines:
            # Mine is clicked
            self.stake = 0
            await self.broadcast_event(events.GameOver(x=event.x, y=event.y))
            return

        self.remaining_mines -= 1
        self.multiplier = self.calculate_multiplier()
        await self.broadcast_event(events.MineClickedResponse(x=event.x, y=event.y, multiplier=self.multiplier))

    @add_event_listener(events.StartGame)
    async def start_game_callback(self, _: events.StartGame, ws: WebsocketClient) -> None:
        self.remaining_mines = 25
        self.num_mines = 4
        self.multiplier = self.calculate_multiplier()
        await self.send_event(events.UpdateMoney(money=self.money), ws)

    @add_event_listener(events.Chashout)
    async def chashout_callback(self, event: events.Chashout, ws: WebsocketClient) -> None:
        self.money += int(self.stake * self.multiplier)
        await self.queries.update_user_money(money=self.money, id_=ws.user_id)
        await self.send_event(events.ChashoutResponse(balance=self.money), ws)
        self.stake = 0
        self.remaining_mines = 25
        self.num_mines = 4
        self.multiplier = self.calculate_multiplier()



    @property
    @typing.override
    def max_num_clients(self) -> int:
        return 1

    @staticmethod
    @typing.override
    def endpoint() -> str:
        return "mines"
