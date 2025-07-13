from __future__ import annotations

import logging
import typing

import arcade
import arcade.gui
from arcade.gui import UIAnchorLayout

from frontend.constants import SCREEN_HEIGHT
from frontend.constants import SCREEN_WIDTH
from frontend.constants import Alignment
from frontend.constants import GameModes
from frontend.internal.decorator import add_event_listener
from frontend.internal.websocket_view import WebsocketView
from frontend.ui import Button
from shared.models import events

if typing.TYPE_CHECKING:
    from frontend.window import MainWindow
logger = logging.getLogger(__name__)


class MinesView(WebsocketView):
    """
    Frontend view for the Mines game mode.
    Authors: Quirin
    """

    def __init__(self, window: MainWindow, game_mode: GameModes, lobby_id: str) -> None:
        super().__init__(window=window, game_mode=game_mode, lobby_id=lobby_id)
        self.ui = arcade.gui.UIManager()
        self._initialize_game_state()
        self.create_stake_controls()
        self.create_mines_field()

    def _initialize_game_state(self) -> None:
        self.stake = 0
        self.balance = 1000
        self.is_game_started = False
        self.mines_field = [[] for _ in range(5)]

    def _update_text_displays(self) -> None:
        self.balance_text.text = f"Balance: {self.balance}"
        self.stake_text.text = f"Stake: {self.stake}"

    def _update_stake(self, amount: int) -> None:
        if (
            (amount > 0 and self.balance < abs(amount))
            or (amount < 0 and self.stake < abs(amount))
            or self.is_game_started
        ):
            return

        self.balance -= amount
        self.stake += amount
        self._update_text_displays()

        stake_event = events.MinesChangeStake(amount=amount)
        self.send_event(stake_event)

    def on_increase_stake(self, _: arcade.gui.UIOnClickEvent) -> None:
        self._update_stake(100)

    def on_decrease_stake(self, _: arcade.gui.UIOnClickEvent) -> None:
        self._update_stake(-100)

    def _toggle_stake_buttons(self, enabled: bool) -> None:
        self.increase_stake.disabled = not enabled
        self.decrease_stake.disabled = not enabled
        self.increase_stake.text = "+ Stake" if enabled else "---"
        self.decrease_stake.text = "- Stake" if enabled else "---"

    def create_stake_controls(self) -> None:
        self.head_line = arcade.gui.UILabel(text="Mines", width=SCREEN_WIDTH, align="center", font_size=25)

        self.stake_anchor = self.ui.add(UIAnchorLayout(width=SCREEN_WIDTH, height=SCREEN_HEIGHT))

        stake_container = arcade.gui.UIBoxLayout(align=Alignment.CENTER, space_between=10, vertical=True)

        text_container = arcade.gui.UIBoxLayout(align=Alignment.CENTER, space_between=20, vertical=False)

        self.stake_text = arcade.gui.UILabel(text=f"Stake: {self.stake}", width=150, align="center", font_size=20)

        self.balance_text = arcade.gui.UILabel(text=f"Balance: {self.balance}", width=150, align="center", font_size=20)

        text_container.add(self.stake_text)
        text_container.add(self.balance_text)

        stake_container.add(text_container)

        self.increase_stake = Button(text="+ Stake", width=150, height=40)
        self.increase_stake.set_handler("on_click", self.on_increase_stake)
        stake_container.add(self.increase_stake)

        self.decrease_stake = Button(text="- Stake", width=150, height=40)
        self.decrease_stake.set_handler("on_click", self.on_decrease_stake)
        stake_container.add(self.decrease_stake)

        self.start_game = Button(text="Start Game", width=200, height=75)
        self.start_game.set_handler("on_click", self.on_start_game)
        stake_container.add(self.start_game)

        self.stake_anchor.add(child=stake_container, anchor_x="left", anchor_y="center", align_x=300)

    def create_mines_field(self) -> None:
        self.mines_anchor = self.ui.add(UIAnchorLayout(width=SCREEN_WIDTH, height=SCREEN_HEIGHT))

        self.box = arcade.gui.UIBoxLayout(align=Alignment.CENTER, space_between=10, vertical=True)

        self.box.add(self.head_line)

        mines_grid = arcade.gui.UIBoxLayout(align=Alignment.CENTER, space_between=10, vertical=False)

        for i in range(5):
            row = arcade.gui.UIBoxLayout(align=Alignment.CENTER, space_between=10)
            for _ in range(5):
                button = Button(text="?", width=75, height=75)
                button.set_handler("on_click", self.on_mine_clicked)
                row.add(button)
                self.mines_field[i].append(button)
            mines_grid.add(row)

        self.box.add(mines_grid)

        self.mines_anchor.add(child=self.box, anchor_x="center", anchor_y="center")

        self.ui.enable()

    @add_event_listener(events.MinesChashoutResponse)
    def new_game(self, event: events.MinesChashoutResponse) -> None:
        self.is_game_started = False
        self.start_game.text = "Start Game"
        self._toggle_stake_buttons(True)
        self.stake = 0
        self.balance = event.balance
        self._update_text_displays()
        self.head_line.text = "Mines"

        for row in self.mines_field:
            for button in row:
                button.text = "?"
                button.disabled = False

    def on_start_game(self, _: arcade.gui.UIOnClickEvent) -> None:
        if not self.is_game_started:
            if self.stake <= 0:
                return
            self.is_game_started = True
            self.start_game.text = "Cash out"
            self.head_line.text = "Multiplier: 1.0"
            self._toggle_stake_buttons(False)
        else:
            self.send_event(events.MinesChashout())

    @add_event_listener(events.UpdateMoney)
    def on_update_money(self, event: events.UpdateMoney) -> None:
        self.balance = event.money
        self.balance_text.text = f"Balance: {self.balance}"

    def on_mine_clicked(self, button: arcade.gui.UIOnClickEvent) -> None:
        if not self.is_game_started:
            return

        # Finde die Position des geklickten Buttons im mines_field
        for i in range(5):
            for j in range(5):
                if self.mines_field[i][j] == button.source:
                    mine_event = events.MinesMineClicked(x=j, y=i)
                    self.send_event(mine_event)

    @add_event_listener(events.MinesMineClickedResponse)
    def on_mine_clicked_response(self, event: events.MinesMineClickedResponse) -> None:
        self.mines_field[event.y][event.x].text = "X"
        self.mines_field[event.y][event.x].disabled = True
        self.head_line.text = f"Multiplier: {event.multiplier:.1f}"

    @add_event_listener(events.MinesGameOver)
    def on_game_over(self, event: events.MinesGameOver) -> None:
        self.start_game.text = "Start Game"
        self.mines_field[event.y][event.x].text = "!"
        self.head_line.text = "Game Over!"

    @property
    @typing.override
    def can_pause(self) -> bool:
        return True

    @typing.override
    def on_draw(self) -> None:
        super().on_draw()
        self.ui.draw()

    @typing.override
    def on_show_view(self) -> None:
        self.ui.enable()

    @typing.override
    def on_hide_view(self) -> None:
        self.ui.disable()
