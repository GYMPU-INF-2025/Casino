from __future__ import annotations

import logging
import typing

import arcade.gui

from frontend import constants as c
from frontend.internal.decorator import add_event_listener
from frontend.internal.websocket_view import WebsocketView
from frontend.ui import BoxLayout
from frontend.ui import Button
from frontend.ui import ButtonStyle
from frontend.ui import InputText
from frontend.ui import Label
from shared.models import events

if typing.TYPE_CHECKING:
    from frontend.window import MainWindow

logger = logging.getLogger(__name__)

DEALER_PILE = 0
OWN_PILE = 1

TOTAL_PILES = 6


PILES_POSITIONS = (
    (c.CENTER_X, 850),
    (c.CENTER_X, 350),
    (c.CENTER_X - 600, 350),
    (c.CENTER_X - 300, 350),
    (c.CENTER_X + 300, 350),
    (c.CENTER_X + 600, 350),
)

CARD_SCALE = 1

CARD_WIDTH = 140 * CARD_SCALE
CARD_HEIGHT = 190 * CARD_SCALE
USERNAME_OFFSET = 120 * CARD_SCALE
MONEY_OFFSET = 160 * CARD_SCALE

CARD_OFFSET = 50 * CARD_SCALE

UNKNOWN_CARD_NAME = "cardBack_red4"


class CardSprite(arcade.Sprite):
    """Class that draws a card to the screen by loading the texture and subclassing `arcade.Sprite`

    Authors: Nina
    """

    def __init__(self, card: str, scale: float = CARD_SCALE) -> None:
        """Card constructor"""

        self.card = card

        self.image_file_name = f":resources:images/cards/{card}.png"

        super().__init__(self.image_file_name, scale, hit_box_algorithm="None")


class BlackjackView(WebsocketView):
    """Blackjack View class displaying the game and handling user interactions.

    Authors: Nina
    """

    def __init__(self, window: MainWindow, game_mode: c.GameModes, lobby_id: str) -> None:
        super().__init__(window, game_mode, lobby_id)

        ### Setup GUI

        self.ui = arcade.gui.UIManager()
        self.anchor = self.ui.add(arcade.gui.UIAnchorLayout())

        ### Setup smaller gui items like money display and start game button

        self.start_button = self.anchor.add(
            anchor_y=c.Alignment.CENTER,
            anchor_x=c.Alignment.CENTER,
            child=Button(text="Start Game", style=ButtonStyle(), width=300, height=80),
        )
        self.start_button.set_handler("on_click", self.on_start_button)
        self.own_money_text = self.anchor.add(
            anchor_x=c.Alignment.CENTER,
            anchor_y=c.Alignment.TOP,
            child=arcade.gui.UILabel(text="Current Money: 0$", font_size=28),
        )
        self.win_text = self.anchor.add(
            anchor_x=c.Alignment.CENTER, anchor_y=c.Alignment.CENTER, child=arcade.gui.UILabel(text="", font_size=48)
        )

        ### Setup menu at the bottom to control the game

        self.box = self.anchor.add(
            anchor_y=c.Alignment.BOTTOM,
            child=BoxLayout(
                space_between=50, align=c.Alignment.RIGHT, vertical=False, size_hint_min=(c.SCREEN_WIDTH, 80)
            ),
        )
        self.box.add(Label(text="Bet:", width=150, font_size=40))
        self.bet_input = self.box.add(InputText(ui_manager=self.ui, width=150, height=80, font_size=40))
        self.bet_input.set_handler("on_change", self.on_bet_change)
        self.set_bet_button = self.box.add(Button(text="Set Bet", style=ButtonStyle(), width=150, height=80))
        self.set_bet_button.set_handler("on_click", self.on_set_bet_button)
        self.hold_card_button = self.box.add(Button(text="Hold", style=ButtonStyle(), width=150, height=80))
        self.hold_card_button.set_handler("on_click", self.on_hold_card_button)
        self.draw_card_button = self.box.add(Button(text="Draw", style=ButtonStyle(), width=150, height=80))
        self.draw_card_button.set_handler("on_click", self.on_draw_card_button)

        ### Make buttons disabled from the beginning and hide menu

        self.draw_card_button.disabled = True
        self.hold_card_button.disabled = True
        self.set_bet_button.disabled = True
        self.bet_input.disabled = True

        self.box.visible = False

        ### Load background texture

        self._blackjack_table = arcade.load_texture(c.ASSETS_PATH / "blackjack" / "blackjack_background.png")

        ### Initialize Sprite list and piles where cards can be stored

        self._card_list = arcade.SpriteList()
        self._piles: list[list[CardSprite]] = [[] for _ in range(TOTAL_PILES)]

        ### Create Text fields

        self._username_texts: list[arcade.Text] = []
        self._money_texts: list[arcade.Text] = []
        self._card_value_texts: list[arcade.Text] = []

        for i, pos in enumerate(PILES_POSITIONS):
            t = arcade.Text(
                x=pos[0],
                y=pos[1] - USERNAME_OFFSET,
                align=c.Alignment.CENTER,
                anchor_x=c.Alignment.CENTER,
                anchor_y=c.Alignment.CENTER,
                font_size=24,
                text="",
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
                text="",
            )
            self._money_texts.append(t)
            t = arcade.Text(
                x=pos[0],
                y=pos[1] + USERNAME_OFFSET,
                align=c.Alignment.CENTER,
                anchor_x=c.Alignment.CENTER,
                anchor_y=c.Alignment.CENTER,
                font_size=24,
                text="",
            )
            self._card_value_texts.append(t)

        ### Game state

        self.own_username = ""
        self.own_money = 0
        self.started = True

    ### Ui Inputs

    def on_bet_change(self, event: arcade.gui.UIOnChangeEvent) -> None:
        """This is being called when the text in the bet text input changes. This function makes sure that you can
        only enter numeric values into the text input. If not it removes the added characters.
        """
        if not isinstance(event.new_value, str) or not isinstance(event.old_value, str) or event.new_value == "":
            return
        if not event.new_value.isnumeric():
            self.bet_input.text = event.old_value

    def on_start_button(self, _: arcade.gui.UIOnClickEvent) -> None:
        """Callback when the start game button is pressed."""
        self.send_event(events.BlackjackStartGame())

    def on_hold_card_button(self, _: arcade.gui.UIOnClickEvent) -> None:
        """Callback when the hold card button is pressed."""
        self.send_event(events.BlackjackHoldCard())

    def on_draw_card_button(self, _: arcade.gui.UIOnClickEvent) -> None:
        """Callback when the draw card button is pressed."""
        self.send_event(events.BlackjackDrawCard())

    def on_set_bet_button(self, _: arcade.gui.UIOnClickEvent) -> None:
        """Callback when the set bet button is pressed.
        If there is a valid text in the input field, it sends the bet to the server.
        """
        if self.bet_input.text == "" or int(self.bet_input.text) == 0:
            return
        self.send_event(events.BlackjackSetBet(bet=int(self.bet_input.text)))

    ### Event Listeners

    @add_event_listener(events.BlackjackPlayerAction)
    def on_player_action_event(self, event: events.BlackjackPlayerAction) -> None:
        """Listener function that is called when a player has to do their action.

        If this player is the player playing on this view, the required inputs are enabled, if not they are be disabled.
        """
        if event.username == self.own_username:
            self.draw_card_button.disabled = False
            self.hold_card_button.disabled = False
        else:
            self.draw_card_button.disabled = True
            self.hold_card_button.disabled = True

    @add_event_listener(events.ReadyEvent)
    def on_ready_event(self, event: events.ReadyEvent) -> None:
        """Listener function that is called when the player joins the lobby. This sets the money and the username."""
        self.own_username = event.user.username
        self.set_own_money(event.user.money)
        self._username_texts[OWN_PILE].text = event.user.username

    @add_event_listener(events.BlackjackDraw)
    def on_draw_event(self, _: events.BlackjackDraw) -> None:
        """Listener function that updates if the player has a draw."""
        self.win_text.text = "Draw! You get your bet amount back!"

    @add_event_listener(events.BlackjackWin)
    def on_win_event(self, _: events.BlackjackWin) -> None:
        """Listener function that updates if the player has won."""
        self.win_text.text = "You have won!"

    @add_event_listener(events.BlackjackDefeat)
    def on_defeat_event(self, _: events.BlackjackDefeat) -> None:
        """Listener function that updates if the player has lost."""
        self.win_text.text = "You have lost!"

    @add_event_listener(events.BlackjackWaitingForBet)
    def on_waiting_for_bet(self, _: events.BlackjackWaitingForBet) -> None:
        """Listener function that updates if the game is waiting for bets.

        All this listener does is enabling the required inputs to input bets.
        """
        self.set_bet_button.disabled = False
        self.bet_input.disabled = False

    @add_event_listener(events.UpdateMoney)
    def on_update_money(self, event: events.UpdateMoney) -> None:
        """Listener function that updates the users money."""
        self.set_own_money(event.money)

    @add_event_listener(events.BlackjackUpdateGame)
    def on_update_game(self, event: events.BlackjackUpdateGame) -> None:
        """Listener function that updates the game state.

        It first resets everything (cards, texts) and then goes through every players data.
        If the game is not started, each player gets 2 unknown cards to display something while they are waiting for the
        game to start. If the game is already started, it goes through every players data and sets their cards, their
        total card value (if they have any cards) and their current bidding amount (if they have already bid).

        If the current user is not in the active players (that means he joined into an ongoing game) his controls will
        bedisabled, and he can watch the other players until a new round starts.
        """
        self.set_started(event.started)
        self.reset_cards()
        self.reset_texts()
        own_playing = False

        player_index = 2
        for player in event.active_players:
            pile_index = player_index
            if player.username == self.own_username:
                own_playing = True
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
                self.add_card_to_pile(card, pile_index)
                self._card_list.append(card)
            if total_card_value != 0:
                self._card_value_texts[pile_index].text = str(total_card_value)

            if player.current_bet != 0:
                self._money_texts[pile_index].text = f"{player.current_bet}$"

                if player.username == self.own_username:
                    self.set_bet_button.disabled = True
                    self.bet_input.disabled = True
                    self.bet_input.text = ""

            if pile_index not in {OWN_PILE, DEALER_PILE}:
                player_index += 1

        if not own_playing:
            self.box.visible = False
            self.set_bet_button.disabled = True
            self.bet_input.disabled = True
            self.bet_input.text = ""
            self.draw_card_button.disabled = True
            self.hold_card_button.disabled = True

    ### Utility Functions

    def add_card_to_pile(self, new_card: CardSprite, pile: int) -> None:
        """Function that adds a card sprite to a pile.

        Each pile has a position and when adding a card to a pile, the position of the card is being set.
        If there are multiple cards in a pile, they are "stacked" so that you only see parts of the lower cards.
        This is being achieved by applying an offset to the position of the cards, which is smaller than the width
        of the cards.
        """
        self._piles[pile].append(new_card)
        total_pile_width = 0
        for i in range(len(self._piles[pile])):
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
        """Helper function that clears the sprite list and empties all the card piles."""
        self._card_list.clear()
        self._piles = [[] for _ in range(TOTAL_PILES)]

    def reset_texts(self) -> None:
        """Helper function to reset all the texts. This function is used before updating the current game state."""
        self.win_text.text = ""
        for i, t in enumerate(self._username_texts):
            if i < 2:  # noqa: PLR2004
                continue
            t.text = ""
        for t in self._money_texts:
            t.text = ""
        for t in self._card_value_texts:
            t.text = ""

    def set_started(self, started: bool) -> None:
        """Helper function to change game state depending on the game_started value sent by the server.

        If the game is not started, we don't want to show the controls at the bottom,
        but we want to show the start game button.
        """
        self.started = started
        self.box.visible = started
        self.start_button.disabled = started
        self.start_button.visible = not started

    def set_own_money(self, money: int) -> None:
        """Helper function used to set the money.
        This also updates the text at the top displaying the current amount of money.
        """
        self.own_money = money
        self.own_money_text.text = f"Current Money: {money}$"

    ### Arcade Events

    @typing.override
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
