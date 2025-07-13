from __future__ import annotations

__all__ = ("Blackjack",)

import typing
import asyncio

from backend.cards import CardStack
from backend.internal.ws import add_event_listener
from backend.internal.ws import GameLobbyBase
from shared.models import events
from sanic.log import logger

if typing.TYPE_CHECKING:
    from backend.db.queries import Queries
    from backend.internal.ws import WebsocketClient


class Blackjack(GameLobbyBase):
    def __init__(self, *, lobby_id: str, queries: Queries) -> None:
        super().__init__(lobby_id=lobby_id, queries=queries)
        self.cards = CardStack()
        self.game_started = False
        self.waiting_for_bets = False
        self.active_players: dict[WebsocketClient, events.BlackjackPlayerData] = {}
        self.waiting_players: dict[WebsocketClient, events.BlackjackPlayerData] = {}
        self.dealer = events.BlackjackPlayerData(
            username=""
        )
        self.hidden_card = events.BlackjackCardData(
            name="",
            value=0
        )

        self.current_waiting_task: None | tuple[int, str,asyncio.Task] = None

    @add_event_listener(events.ReadyEvent)
    async def on_ready(self, _: events.ReadyEvent, ws: WebsocketClient) -> None:
        user = await self.get_user_by_client(ws)
        if self.game_started:
            self.waiting_players[ws] = events.BlackjackPlayerData(username=user.username)
        else:
            self.active_players[ws] = events.BlackjackPlayerData(username=user.username)
        await self.broadcast_update()

    async def reset_game(self) -> None:
        self.cards.recreate_card_stack()
        self.game_started = False
        self.waiting_for_bets = False
        self.dealer = events.BlackjackPlayerData(
            username=""
        )
        self.hidden_card = events.BlackjackCardData(
            name="",
            value=0
        )
        self.current_waiting_task = None
        for p_data in self.active_players.values():
            p_data.current_bet = 0
            p_data.cards = []
        await self.broadcast_update()

    @add_event_listener(events.LeaveEvent)
    async def on_leave(self, _: events.LeaveEvent, ws: WebsocketClient) -> None:
        self.waiting_players.pop(ws, None)
        self.active_players.pop(ws, None)
        if len(self._clients) == 0:
            await self.reset_game()
        await self.broadcast_update()

    async def broadcast_update(self) -> None:
        active_players = list(self.active_players.values())
        active_players.append(self.dealer)
        await self.broadcast_event(events.BlackjackUpdateGame(started=self.game_started, active_players=active_players, waiting_players=list(self.waiting_players.values())))

    @add_event_listener(events.BlackjackSetBet)
    async def on_set_bet(self, event: events.BlackjackSetBet, ws: WebsocketClient) -> None:
        if not self.waiting_for_bets:
            return
        if (player_data := self.active_players.get(ws)) is None:
            logger.warning("waiting player tried setting bet! %s", ws)
            return
        if player_data.current_bet != 0:
            logger.debug("player tried setting bet even though he already did! %s", ws)
            return
        user_money = (await self.get_user_by_client(ws)).money
        if event.bet > user_money:
            logger.debug("player tried setting bet to high! %s", ws)
            return
        player_data.current_bet = event.bet
        await self.broadcast_update()
        await self.queries.update_user_money(money=user_money-event.bet, id_=ws.user_id)
        await self.queries.conn.commit()
        await self.send_event(events.UpdateMoney(money=user_money-event.bet), ws)

        all_finished = True
        for p_data in self.active_players.values():
            if p_data.current_bet == 0:
                all_finished = False

        if all_finished:
            self.waiting_for_bets = False
            asyncio.create_task(self.start_giving_cards())

    def get_card_value(self, card: str) -> tuple[int, bool]:
        last_letter = card[-1]
        if last_letter.isnumeric():
            if last_letter == "0":
                return 10, False
            else:
                return int(last_letter), False
        if last_letter != "A":
            return 10, False
        return 11, True

    async def start_giving_cards(self) -> None:
        sleep_duration = 0.65

        for i in range(2):
            card = self.cards.give_card()
            value, ace = self.get_card_value(card.name)
            card_data = events.BlackjackCardData(
                name = card.name,
                value=value
            )
            if i == 1:
                self.hidden_card = card_data
                self.dealer.cards.append(events.BlackjackCardData(
                        name="",
                        value=0
                    )
                )
            else:
                self.dealer.cards.append(card_data)

            await self.broadcast_update()
            await asyncio.sleep(sleep_duration)

            for p_data in self.active_players.values():
                card = self.cards.give_card()
                value, ace = self.get_card_value(card.name)
                card_data = events.BlackjackCardData(
                    name=card.name,
                    value=value
                )
                p_data.cards.append(card_data)
                await self.broadcast_update()
                await asyncio.sleep(sleep_duration)

        player_one = list(self.active_players.values())[0]
        await self.broadcast_event(events.BlackjackPlayerAction(username=player_one.username))
        waiting_task = asyncio.create_task(self.player_action_timeout(0))
        self.current_waiting_task = (0, player_one.username, waiting_task)


    async def dealers_turn(self) -> None:
        await self.broadcast_event(events.BlackjackPlayerAction(username=""))
        self.dealer.cards.pop(len(self.dealer.cards) -1)
        self.dealer.cards.append(self.hidden_card)
        await self.broadcast_update()

        while True:
            total_value = 0
            for c in self.dealer.cards:
                total_value += c.value
            if total_value <= 16:
                card = self.cards.give_card()
                value, ace = self.get_card_value(card.name)
                card_data = events.BlackjackCardData(
                    name=card.name,
                    value=value
                )
                self.dealer.cards.append(card_data)
                await self.broadcast_update()
            else:
                break
        await self.evaluate_wins()


    async def next_players_turn(self, player_num: int) -> None:
        if self.current_waiting_task is not None:
            task = self.current_waiting_task[2]
            if task.done():
                return
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            self.current_waiting_task = None
        player_list = list(self.active_players.values())

        if len(player_list) == player_num:
            await self.dealers_turn()
            return
        player = list(self.active_players.values())[player_num]
        await self.broadcast_event(events.BlackjackPlayerAction(username=player.username))
        waiting_task = asyncio.create_task(self.player_action_timeout(player_num))
        self.current_waiting_task = (player_num, player.username, waiting_task)

    async def player_action_timeout(self, player_num: int) -> None:
        await asyncio.sleep(7.5)
        self.current_waiting_task = None
        await self.next_players_turn(player_num+1)


    @add_event_listener(events.BlackjackHoldCard)
    async def on_hold_card(self, _: events.BlackjackHoldCard, ws: WebsocketClient) -> None:
        if self.active_players[ws].username != self.current_waiting_task[1]:
            return

        if self.current_waiting_task is None:
            return
        await self.next_players_turn(self.current_waiting_task[0] + 1)

    def get_total_card_value(self, cards: list[events.BlackjackCardData]) -> int:
        total_value = 0
        for c in cards:
            total_value += c.value
        return total_value

    @add_event_listener(events.BlackjackDrawCard)
    async def on_draw_card(self, _: events.BlackjackHoldCard, ws: WebsocketClient) -> None:
        if self.active_players[ws].username != self.current_waiting_task[1]:
            return

        if self.current_waiting_task is None:
            return
        card = self.cards.give_card()
        value, ace = self.get_card_value(card.name)
        card_data = events.BlackjackCardData(
            name=card.name,
            value=value
        )
        self.active_players[ws].cards.append(card_data)
        await self.broadcast_update()
        if self.get_total_card_value(self.active_players[ws].cards) >= 21:
            await self.next_players_turn(self.current_waiting_task[0] + 1)
        else:
            await self.next_players_turn(self.current_waiting_task[0])

    async def wait_for_end_game(self) -> None:
        await asyncio.sleep(5)
        await self.reset_game()

    async def evaluate_wins(self) -> None:
        total_dealer = self.get_total_card_value(self.dealer.cards)
        for ws, p_data in self.active_players.items():
            total = self.get_total_card_value(p_data.cards)
            users_money = (await self.queries.get_user_by_id(id_=ws.user_id)).money
            if total > 21:
                await self.send_event(events.BlackjackDefeat(), ws)
            elif total == total_dealer:
                await self.send_event(events.BlackjackDraw(), ws)
                await self.queries.update_user_money(money = users_money + p_data.current_bet, id_=ws.user_id)
                await self.send_event(events.UpdateMoney(money=users_money + p_data.current_bet), ws)
            elif total > total_dealer or total_dealer > 21:
                await self.send_event(events.BlackjackWin(), ws)
                await self.queries.update_user_money(money = users_money + p_data.current_bet * 2, id_=ws.user_id)
                await self.send_event(events.UpdateMoney(money=users_money + p_data.current_bet * 2), ws)
            else:
                await self.send_event(events.BlackjackDefeat(), ws)
        await self.queries.conn.commit()
        asyncio.create_task(self.wait_for_end_game())

    async def wait_for_bets(self) -> None:
        wait_time = 10
        await self.broadcast_event(events.BlackjackWaitingForBet(wait_time=wait_time))
        await asyncio.sleep(wait_time)
        if not self.waiting_for_bets:
            return
        self.waiting_for_bets = False
        for ws, p_data in self.active_players.items():
            if p_data.current_bet != 0:
                continue
            p_data.current_bet = 10
            user_money = (await self.queries.get_user_by_id(id_=ws.user_id)).money
            await self.queries.update_user_money(money=user_money-p_data.current_bet, id_=ws.user_id)
            await self.queries.conn.commit()
            await self.send_event(events.UpdateMoney(money=user_money-p_data.current_bet), ws)
        await self.broadcast_update()
        asyncio.create_task(self.start_giving_cards())

    @add_event_listener(events.BlackjackStartGame)
    async def on_start(self, _: events.BlackjackStartGame, ws: WebsocketClient) -> None:
        self.game_started = True

        await self.broadcast_update()
        self.waiting_for_bets = True
        asyncio.create_task(self.wait_for_bets())



    @property
    @typing.override
    def max_num_clients(self) -> int:
        return 5

    @staticmethod
    @typing.override
    def endpoint() -> str:
        return "blackjack"