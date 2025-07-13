from __future__ import annotations

import copy
import logging
import typing

import arcade.gui
from frontend.internal.decorator import add_event_listener

from frontend.internal.websocket_view import WebsocketView
from frontend.ui import Button, ButtonStyle, BoxLayout, InputText, Label
from shared.models import events
from frontend import constants as c

if typing.TYPE_CHECKING:
    from frontend.window import MainWindow

logger = logging.getLogger(__name__)

DEALER_PILE = 0
OWN_PILE = 1

TOTAL_PILES = 6


PILES_POSITIONS = (
    (c.CENTER_X,850),
    (c.CENTER_X,350),
    (c.CENTER_X - 600,350),
    (c.CENTER_X - 300,350),
    (c.CENTER_X + 300,350),
    (c.CENTER_X + 600,350),
)

# Constants for sizing
CARD_SCALE = 1

# How big are the cards?
CARD_WIDTH = 140 * CARD_SCALE
CARD_HEIGHT = 190 * CARD_SCALE
USERNAME_OFFSET = 120 * CARD_SCALE
MONEY_OFFSET = 160 * CARD_SCALE

CARD_OFFSET = 50 * CARD_SCALE

UNKNOWN_CARD_NAME = "cardBack_red4"

class CardSprite(arcade.Sprite):

    def __init__(self, card: str, scale: float = CARD_SCALE):
        """ Card constructor """

        self.card = card

        self.image_file_name = f":resources:images/cards/{card}.png"

        super().__init__(self.image_file_name, scale, hit_box_algorithm="None")

class BlackjackView(WebsocketView):

    def __init__(self, window: MainWindow, game_mode: c.GameModes, lobby_id: str) -> None:
        super().__init__(window, game_mode, lobby_id)

        ### Setup GUI

        self.ui = arcade.gui.UIManager()
        self.anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        self.start_button = self.anchor.add(anchor_y=c.Alignment.CENTER, anchor_x=c.Alignment.CENTER, child=Button(text="Start Game", style=ButtonStyle(), width=300, height=80))
        self.start_button.set_handler("on_click", self.on_start_button)
        self.own_money_text = self.anchor.add(anchor_x=c.Alignment.CENTER, anchor_y=c.Alignment.TOP, child=arcade.gui.UILabel(text="Current Money: 0$", font_size=28))
        self.win_text = self.anchor.add(anchor_x=c.Alignment.CENTER, anchor_y=c.Alignment.CENTER, child=arcade.gui.UILabel(text="", font_size=48))


        self.box = self.anchor.add(anchor_y=c.Alignment.BOTTOM, child=BoxLayout(space_between=50, align=c.Alignment.RIGHT, vertical=False, size_hint_min=(c.SCREEN_WIDTH, 80)))
        self.box.add(Label(text="Bet:", width=150, font_size=40))
        self.bet_input = self.box.add(InputText(ui_manager=self.ui, width=150, height=80, font_size=40))
        self.bet_input.set_handler("on_change", self.on_bet_change)
        self.confirm_bet_button = self.box.add(Button(text="Set Bet", style=ButtonStyle(), width=150, height=80))
        self.confirm_bet_button.set_handler("on_click", self.on_confirm_bet_button)
        self.hold_card_button = self.box.add(Button(text="Hold", style=ButtonStyle(), width=150, height=80))
        self.hold_card_button.set_handler("on_click", self.on_hold_card_button)
        self.draw_card_button = self.box.add(Button(text="Draw", style=ButtonStyle(), width=150, height=80))
        self.draw_card_button.set_handler("on_click", self.on_draw_card_button)

        self.draw_card_button.disabled = True
        self.hold_card_button.disabled = True

        self.box.visible = False

        self._blackjack_table = arcade.load_texture(c.ASSETS_PATH / "blackjack" / "blackjack_background.png")
        self._card_list = arcade.SpriteList()

        self._piles: list[list[CardSprite]] = [[] for _ in range(TOTAL_PILES)]
        self._username_texts: list[arcade.Text] = []
        self._money_texts: list[arcade.Text] = []
        self._card_value_texts: list[arcade.Text] = []
        self.started = True


        ### Create Text fields

        for i, pos in enumerate(PILES_POSITIONS):
            t = arcade.Text(
                x = pos[0],
                y=pos[1] - USERNAME_OFFSET,
                align=c.Alignment.CENTER,
                anchor_x=c.Alignment.CENTER,
                anchor_y=c.Alignment.CENTER,
                font_size=24,
                text=""
            )
            if i == 0:
                t.text = "Dealer"
            self._username_texts.append(t)
            t = arcade.Text(
                x=pos[0],
                y=pos[1] - MONEY_OFFSET,
                align=c.Alignment.CENTER,
                anchor_x=c.Alignment.CENTER,
                anchor_y=c.Alignment.CENTER,
                font_size=24,
                text=""
            )
            self._money_texts.append(t)
            t = arcade.Text(
                x=pos[0],
                y=pos[1] + USERNAME_OFFSET,
                align=c.Alignment.CENTER,
                anchor_x=c.Alignment.CENTER,
                anchor_y=c.Alignment.CENTER,
                font_size=24,
                text=""
            )
            self._card_value_texts.append(t)

        self.own_username = ""
        self.own_money = 0

    def on_bet_change(self, event: arcade.gui.UIOnChangeEvent) -> None:
        if not isinstance(event.new_value, str) or not isinstance(event.old_value, str) or event.new_value == "":
            return
        if not event.new_value.isnumeric():
            self.bet_input.text = event.old_value

    @add_event_listener(events.BlackjackPlayerAction)
    def on_player_action_event(self, event: events.BlackjackPlayerAction) -> None:
        if event.username == self.own_username:
            self.draw_card_button.disabled = False
            self.hold_card_button.disabled = False
        else:
            self.draw_card_button.disabled = True
            self.hold_card_button.disabled = True

    @add_event_listener(events.ReadyEvent)
    def on_ready_event(self, event: events.ReadyEvent):
        self.own_username = event.user.username
        self.set_own_money(event.user.money)
        self._username_texts[OWN_PILE].text = event.user.username

    @add_event_listener(events.BlackjackDraw)
    def on_draw_event(self, _: events.BlackjackDraw):
        self.win_text.text = "Draw! You get your bet amount back!"

    @add_event_listener(events.BlackjackWin)
    def on_win_event(self, _: events.BlackjackWin):
        self.win_text.text = "You have won!"

    @add_event_listener(events.BlackjackDefeat)
    def on_defeat_event(self, _: events.BlackjackDefeat):
        self.win_text.text = "You have lost!"


    def add_card_to_pile(self, card: CardSprite, pile: int):
        self._piles[pile].append(card)
        total_pile_width = 0
        for i, card in enumerate(self._piles[pile]):
            if i == 0:
                total_pile_width += CARD_WIDTH
            else:
                total_pile_width += CARD_OFFSET
        card_x_pos = PILES_POSITIONS[pile][0] - total_pile_width // 2
        half_card = CARD_WIDTH // 2
        for card in self._piles[pile]:
            card.center_y = PILES_POSITIONS[pile][1]
            card.center_x = card_x_pos + half_card
            card_x_pos += CARD_OFFSET

    def reset_cards(self) -> None:
        self._card_list.clear()
        self._piles = [[] for _ in range(TOTAL_PILES)]

    def reset_texts(self) -> None:
        self.win_text.text = ""
        for i, t in enumerate(self._username_texts):
            if i < 2:
                continue
            t.text = ""
        for i, t in enumerate(self._money_texts):
            t.text = ""
        for i, t in enumerate(self._card_value_texts):
            t.text = ""

    @add_event_listener(events.BlackjackWaitingForBet)
    def on_waiting_for_bet(self, _: events.BlackjackWaitingForBet) -> None:
        self.confirm_bet_button.disabled = False
        self.bet_input.disabled = False

    @add_event_listener(events.UpdateMoney)
    def on_update_money(self, event: events.UpdateMoney) -> None:
        self.set_own_money(event.money)


    @add_event_listener(events.BlackjackUpdateGame)
    def on_update_game(self, event: events.BlackjackUpdateGame) -> None:
        """Update the games state.


        """
        self.set_started(event.started)
        self.reset_cards()
        self.reset_texts()

        player_index = 2
        for player in event.active_players:
            pile_index = player_index
            if player.username == self.own_username:
                pile_index = OWN_PILE
            elif player.username == "":
                pile_index = DEALER_PILE
            else:
                self._username_texts[pile_index].text = player.username
            if not event.started:
                card1 = CardSprite(UNKNOWN_CARD_NAME)
                card2 = CardSprite(UNKNOWN_CARD_NAME)
                self.add_card_to_pile(card1, pile_index)
                self.add_card_to_pile(card2, pile_index)
                self._card_list.append(card1)
                self._card_list.append(card2)
                continue

            total_card_value = 0
            for card_data in player.cards:
                total_card_value += card_data.value
                card_name = card_data.name
                if card_name == "":
                    card_name = UNKNOWN_CARD_NAME
                card = CardSprite(card_name)
                self.add_card_to_pile(card,pile_index)
                self._card_list.append(card)
            if total_card_value != 0:
                self._card_value_texts[pile_index].text = str(total_card_value)

            if player.current_bet != 0:
                self._money_texts[pile_index].text = f"{player.current_bet}$"

                if player.username == self.own_username:
                    self.confirm_bet_button.disabled = True
                    self.bet_input.disabled = True
                    self.bet_input.text = ""

            if pile_index != OWN_PILE and pile_index != DEALER_PILE:
                player_index += 1


    def set_started(self, started: bool) -> None:
        self.started = started
        self.box.visible = started
        self.start_button.disabled = started
        self.start_button.visible = not started

    def set_own_money(self, money: int) -> None:
        self.own_money = money
        self.own_money_text.text = f"Current Money: {money}$"

    def on_start_button(self, _: arcade.gui.UIOnClickEvent) -> None:
        self.send_event(events.BlackjackStartGame())

    def on_hold_card_button(self, _: arcade.gui.UIOnClickEvent) -> None:
        self.send_event(events.BlackjackHoldCard())

    def on_draw_card_button(self, _: arcade.gui.UIOnClickEvent) -> None:
        self.send_event(events.BlackjackDrawCard())

    def on_confirm_bet_button(self, _: arcade.gui.UIOnClickEvent) -> None:
        if self.bet_input.text == "" or int(self.bet_input.text) == 0:
            return
        self.send_event(events.BlackjackSetBet(bet=int(self.bet_input.text)))

    def on_draw(self) -> bool | None:
        self.clear()
        arcade.draw_texture_rect(self._blackjack_table, self.window.rect)
        self._card_list.draw()
        for t in self._username_texts:
            t.draw()
        for t in self._money_texts:
            t.draw()
        for t in self._card_value_texts:
            t.draw()
        self.ui.draw()


    @typing.override
    def on_show_view(self) -> None:
        self.ui.enable()

    @typing.override
    def on_hide_view(self) -> None:
        self.ui.disable()


    
