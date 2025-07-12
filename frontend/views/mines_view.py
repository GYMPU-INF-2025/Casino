from __future__ import annotations

import logging
import typing

import arcade
import arcade.gui
from arcade.gui import UIAnchorLayout

from frontend.ui import Button
from frontend.constants import SCREEN_HEIGHT, SCREEN_WIDTH, Alignment, GameModes
from frontend.internal.websocket_view import WebsocketView

if typing.TYPE_CHECKING:
    from frontend.window import MainWindow
logger = logging.getLogger(__name__)


class MinesView(WebsocketView):
    def __init__(self, window: MainWindow, game_mode: GameModes, lobby_id: str) -> None:
        super().__init__(window=window, game_mode=game_mode, lobby_id=lobby_id)
        self.ui = arcade.gui.UIManager()

        self.stake = 0
        self.balance = 0
        self.start_game = Button()
        self.mines_field = [[] for _ in range(5)]

        # Erstelle separate Anchors für die verschiedenen UI-Bereiche
        self.mines_anchor = None
        self.stake_anchor = None

        self.create_stake_controls()
        self.create_mines_field()

    def create_stake_controls(self) -> None:
        # Erstelle einen neuen Anchor für die Stake-Kontrollen
        self.stake_anchor = self.ui.add(UIAnchorLayout(width=SCREEN_WIDTH, height=SCREEN_HEIGHT))

        # Container für Stake-Controls
        stake_container = arcade.gui.UIBoxLayout(
            align=Alignment.CENTER,
            space_between=10,
            vertical=True
        )

        self.stake_text = arcade.gui.UILabel(
            text=f"Stake: {self.stake}",
            width=150,
            align="center"
        )
        stake_container.add(self.stake_text)

        increase_stake = Button(
            text="+ Stake",
        )
        increase_stake.on_click = self.on_increase_stake
        stake_container.add(increase_stake)

        decrease_stake = Button(
            text="- Stake",
        )
        decrease_stake.on_click = self.on_decrease_stake
        stake_container.add(decrease_stake)

        # Füge den Container zum Anchor hinzu und positioniere ihn links
        self.stake_anchor.add(
            child=stake_container,
            anchor_x="left",
            anchor_y="center",
            align_x=150
        )

    def create_mines_field(self) -> None:
        self.mines_anchor = self.ui.add(UIAnchorLayout(width=SCREEN_WIDTH, height=SCREEN_HEIGHT))

        self.box = arcade.gui.UIBoxLayout(
            align=Alignment.CENTER,
            space_between=10,
            vertical=False
        )

        for i in range(5):
            row = arcade.gui.UIBoxLayout(align=Alignment.CENTER, space_between=10)
            for j in range(5):
                button = Button(text="?", width=75, height=75)
                row.add(button)
                self.mines_field[i].append(button)
            self.box.add(row)

        self.mines_anchor.add(
            child=self.box,
            anchor_x="center",
            anchor_y="center"
        )

        self.ui.enable()

    def on_increase_stake(self, event) -> None:
        self.stake += 1
        self.stake_text.text = f"Stake: {self.stake}"

    def on_decrease_stake(self, event) -> None:
        if self.stake > 0:
            self.stake -= 1
            self.stake_text.text = f"Stake: {self.stake}"

    @property
    @typing.override
    def can_pause(self) -> bool:
        return True

    def on_draw(self) -> None:
        super().on_draw()
        self.ui.draw()

    def on_show_view(self) -> None:
        self.ui.enable()

    def on_hide_view(self) -> None:
        self.ui.disable()
