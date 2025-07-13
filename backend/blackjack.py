from __future__ import annotations

__all__ = ("Blackjack",)

import asyncio
import contextlib
import typing

from sanic.log import logger

from backend.cards import CardStack
from backend.internal.ws import GameLobbyBase
from backend.internal.ws import add_event_listener
from shared.models import events

if typing.TYPE_CHECKING:
    from backend.db.queries import Queries
    from backend.internal.ws import WebsocketClient


def get_card_value(card: str) -> int:
    """Helper method to get the value of a card.

    Authors: Nina
    """
    last_letter = card[-1]
    if last_letter.isnumeric():
        if last_letter == "0":
            return 10
        return int(last_letter)
    if last_letter != "A":
        return 10
    return 11


def get_total_card_value(cards: list[events.BlackjackCardData]) -> int:
    """Helper method to get the total value of multiple cards.

    Authors: Nina
    """
    total_value = 0
    for c in cards:
        total_value += c.value
    return total_value


class Blackjack(GameLobbyBase):
    """Blackjack lobby class handling all the logic behind the blackjack game.

    Authors: Nina
    """

    def __init__(self, *, lobby_id: str, queries: Queries) -> None:
        super().__init__(lobby_id=lobby_id, queries=queries)
        self.cards = CardStack()
        self.game_started = False
        self.waiting_for_bets = False
        self.active_players: dict[WebsocketClient, events.BlackjackPlayerData] = {}
        self.waiting_players: dict[WebsocketClient, events.BlackjackPlayerData] = {}
        self.dealer = events.BlackjackPlayerData(username="")
        self.hidden_card = events.BlackjackCardData(name="", value=0)

        self.current_waiting_task: None | tuple[int, str, asyncio.Task] = None
        self.background_tasks: set[asyncio.Task] = set()

    ### Event Listeners

    @add_event_listener(events.ReadyEvent)
    async def on_ready(self, _: events.ReadyEvent, ws: WebsocketClient) -> None:
        """Listener when a new client joins the lobby. If the game has already started the client will be put on a
        "waiting" list and if the game has not started he will be put into the active players.
        """
        user = await self.get_user_by_client(ws)
        if self.game_started:
            self.waiting_players[ws] = events.BlackjackPlayerData(username=user.username)
        else:
            self.active_players[ws] = events.BlackjackPlayerData(username=user.username)
        await self.broadcast_update()

    @add_event_listener(events.LeaveEvent)
    async def on_leave(self, _: events.LeaveEvent, ws: WebsocketClient) -> None:
        """Listener when a client leaves the lobby. He will be removed from waiting and active players and if he was
        the only client left in the lobby, everything will be reset after he left.
        """
        self.waiting_players.pop(ws, None)
        self.active_players.pop(ws, None)
        if len(self._clients) == 0:
            await self.reset_game()
        await self.broadcast_update()

    @add_event_listener(events.BlackjackSetBet)
    async def on_set_bet(self, event: events.BlackjackSetBet, ws: WebsocketClient) -> None:
        """Listener when a client sets his bet.

        It first checks if we are currently waiting for new bets and if
        everything looks good the bet will be set and the money will be removed from his account.

        If he was the last one with a missing bet, the game can begin.
        """
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
        await self.queries.update_user_money(money=user_money - event.bet, id_=ws.user_id)
        await self.queries.conn.commit()
        await self.send_event(events.UpdateMoney(money=user_money - event.bet), ws)

        all_finished = True
        for p_data in self.active_players.values():
            if p_data.current_bet == 0:
                all_finished = False

        if all_finished:
            self.waiting_for_bets = False
            task = asyncio.create_task(self.start_giving_cards())
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

    @add_event_listener(events.BlackjackHoldCard)
    async def on_hold_card(self, _: events.BlackjackHoldCard, ws: WebsocketClient) -> None:
        """Listener when a user wants to hold his card. All this does is continuing with the next player and waiting
        for his action.
        """
        if self.current_waiting_task is None:
            return

        if self.active_players[ws].username != self.current_waiting_task[1]:
            return

        await self.next_players_turn(self.current_waiting_task[0] + 1)

    @add_event_listener(events.BlackjackDrawCard)
    async def on_draw_card(self, _: events.BlackjackDrawCard, ws: WebsocketClient) -> None:
        """Listener when a user wants to draw another card. This function draws a card from the card stack and gives
        it to the user, and if the total value of his cards exceed 21, the next player continues."""
        if self.current_waiting_task is None:
            return
        if self.active_players[ws].username != self.current_waiting_task[1]:
            return

        card = self.cards.give_card()
        value = get_card_value(card.name)
        card_data = events.BlackjackCardData(name=card.name, value=value)
        self.active_players[ws].cards.append(card_data)
        await self.broadcast_update()
        if get_total_card_value(self.active_players[ws].cards) >= 21:
            await self.next_players_turn(self.current_waiting_task[0] + 1)
        else:
            await self.next_players_turn(self.current_waiting_task[0])

    @add_event_listener(events.BlackjackStartGame)
    async def on_start(self, _: events.BlackjackStartGame, __: WebsocketClient) -> None:
        """Listener when a user starts the game. This moves all waiting players into the active players list and
        starts waiting for bets.
        """
        for ws, data in self.waiting_players.items():
            self.active_players[ws] = data
        self.waiting_players = {}
        self.game_started = True

        await self.broadcast_update()
        self.waiting_for_bets = True
        task = asyncio.create_task(self.wait_for_bets())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    async def reset_game(self) -> None:
        """Function used to reset the game state.
        This is used when the game is over or when every player left the lobby.
        """
        self.cards.recreate_card_stack()
        self.game_started = False
        self.waiting_for_bets = False
        self.dealer = events.BlackjackPlayerData(username="")
        self.hidden_card = events.BlackjackCardData(name="", value=0)
        self.current_waiting_task = None
        for p_data in self.active_players.values():
            p_data.current_bet = 0
            p_data.cards = []
        await self.broadcast_update()

    async def broadcast_update(self) -> None:
        """Helper function to broadcast the current game state."""
        active_players = list(self.active_players.values())
        active_players.append(self.dealer)
        await self.broadcast_event(
            events.BlackjackUpdateGame(
                started=self.game_started,
                active_players=active_players,
                waiting_players=list(self.waiting_players.values()),
            )
        )

    async def start_giving_cards(self) -> None:
        """Function that draws cards and gives them to every player. Everyone gets 2 cards, but the second card of the
        dealer is not visible to the players. After every player received their 2 cards, we start waiting for actions of
        the players."""
        sleep_duration = 0.65

        for i in range(2):
            card = self.cards.give_card()
            value = get_card_value(card.name)
            card_data = events.BlackjackCardData(name=card.name, value=value)
            if i == 1:
                self.hidden_card = card_data
                self.dealer.cards.append(events.BlackjackCardData(name="", value=0))
            else:
                self.dealer.cards.append(card_data)

            await self.broadcast_update()
            await asyncio.sleep(sleep_duration)

            for p_data in self.active_players.values():
                card = self.cards.give_card()
                value = get_card_value(card.name)
                card_data = events.BlackjackCardData(name=card.name, value=value)
                p_data.cards.append(card_data)
                await self.broadcast_update()
                await asyncio.sleep(sleep_duration)

        player_one = next(iter(self.active_players.values()))
        await self.broadcast_event(events.BlackjackPlayerAction(username=player_one.username))
        waiting_task = asyncio.create_task(self.player_action_timeout(0))
        self.current_waiting_task = (0, player_one.username, waiting_task)

    async def dealers_turn(self) -> None:
        """This function is called when the dealer has his turn. He draws cards as long his total value is under/or 16
        and after that he holds. After that we check for wins of each player.
        """
        await self.broadcast_event(events.BlackjackPlayerAction(username=""))
        self.dealer.cards.pop(len(self.dealer.cards) - 1)
        self.dealer.cards.append(self.hidden_card)
        await self.broadcast_update()

        while True:
            total_value = get_total_card_value(self.dealer.cards)
            if total_value <= 16:
                card = self.cards.give_card()
                value = get_card_value(card.name)
                card_data = events.BlackjackCardData(name=card.name, value=value)
                self.dealer.cards.append(card_data)
                await self.broadcast_update()
            else:
                break
        await self.evaluate_wins()

    async def next_players_turn(self, player_num: int) -> None:
        """Function that handles which player can do actions.

        This is achieved by holding the current player as an index `player_num`. After this function got called,
        the player gets an event signalizing that it's his turn. If he makes an action then this function will be called
        again either with his own index or with the index of the next player. This function also creates a task that
        waits 7.5 seconds and if the player didn't do any action in this time, this function will be called for the
        next player. Every time this function gets called it checks for an existing waiting task and cancels it if
        possible and checks if its the dealers turn (every other player has made their action already).
        """
        if self.current_waiting_task is not None:
            task = self.current_waiting_task[2]
            if task.done():
                return
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
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
        """Task used by the `next_players_turn` function to continue with the next player if the current one didn't do
        any actions after 7.5 seconds
        """
        await asyncio.sleep(7.5)
        self.current_waiting_task = None
        await self.next_players_turn(player_num + 1)

    async def wait_for_end_game(self) -> None:
        """Task that sleeps 5 seconds after every game until the game will be reset."""
        await asyncio.sleep(5)
        await self.reset_game()

    async def evaluate_wins(self) -> None:
        """Function called after the dealer made his turn to check which player has won/lost.
        Also updates the money for players that have won/drawn.
        """
        total_dealer = get_total_card_value(self.dealer.cards)
        for ws, p_data in self.active_players.items():
            total = get_total_card_value(p_data.cards)
            users_money = (await self.get_user_by_client(ws)).money
            if total > 21:
                await self.send_event(events.BlackjackDefeat(), ws)
            elif total == total_dealer:
                await self.send_event(events.BlackjackDraw(), ws)
                await self.queries.update_user_money(money=users_money + p_data.current_bet, id_=ws.user_id)
                await self.send_event(events.UpdateMoney(money=users_money + p_data.current_bet), ws)
            elif total > total_dealer or total_dealer > 21:
                await self.send_event(events.BlackjackWin(), ws)
                await self.queries.update_user_money(money=users_money + p_data.current_bet * 2, id_=ws.user_id)
                await self.send_event(events.UpdateMoney(money=users_money + p_data.current_bet * 2), ws)
            else:
                await self.send_event(events.BlackjackDefeat(), ws)
        await self.queries.conn.commit()
        task = asyncio.create_task(self.wait_for_end_game())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    async def wait_for_bets(self) -> None:
        """Task that waits for incoming bets. If at the end of the waiting some players didnt bet, they will get an
        automatic bet of 10$.
        """
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
            user_money = (await self.get_user_by_client(ws)).money
            await self.queries.update_user_money(money=user_money - p_data.current_bet, id_=ws.user_id)
            await self.queries.conn.commit()
            await self.send_event(events.UpdateMoney(money=user_money - p_data.current_bet), ws)
        await self.broadcast_update()
        task = asyncio.create_task(self.start_giving_cards())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    @property
    @typing.override
    def max_num_clients(self) -> int:
        return 5

    @staticmethod
    @typing.override
    def endpoint() -> str:
        return "blackjack"
