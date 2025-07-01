from __future__ import annotations

import logging
import typing

import arcade
import arcade.gui
import arcade.gui.experimental
from arcade.types import Color

import frontend.constants as c
from frontend.ui import BoxLayout
from frontend.ui import Button
from frontend.ui import ButtonStyle
from frontend.ui import Label
from frontend.views.base import BaseGUI


from frontend.views.base import BaseGUI

if typing.TYPE_CHECKING:
    from frontend.window import MainWindow
    from shared.models import responses

logger = logging.getLogger(__name__)


class ChickengameView(BaseGUI):
    def __init__(self, window: MainWindow, game_mode: c.GameModes) -> None:
        super().__init__(window=window)

        self._button_width = (c.MENU_WIDTH - c.MENU_SPACING) / 8
        self._steps_width = (c.MENU_WIDTH - c.MENU_SPACING) / 21
        self.stake = int(0)
        self.money = int(0)

        self.grid = arcade.gui.UIGridLayout(
            column_count=0, row_count=2, horizontal_spacing=c.MENU_SPACING, vertical_spacing=c.MENU_SPACING
        )
        self.anchor = self.ui.add(arcade.gui.UIAnchorLayout())

        self.steps = arcade.gui.UIGridLayout(
            column_count=20, row_count=0, horizontal_spacing=c.MENU_SPACING, vertical_spacing=c.MENU_SPACING
        )
        self.select = arcade.gui.UIGridLayout(
            column_count=7, row_count=0, horizontal_spacing=c.MENU_SPACING, vertical_spacing=c.MENU_SPACING
        )
        self.money = arcade.gui.UIGridLayout(
            column_count=1, row_count=0, horizontal_spacing=c.MENU_SPACING, vertical_spacing=c.MENU_SPACING
        )

        minus = arcade.gui.UIFlatButton(text="-100", width=self._button_width)
        plus = arcade.gui.UIFlatButton(text="+100", width=self._button_width)
        diff_easy = arcade.gui.UIFlatButton(text="Easy", width=self._button_width)
        diff_mid = arcade.gui.UIFlatButton(text="Medium", width=self._button_width)
        diff_hard = arcade.gui.UIFlatButton(text="Hard", width=self._button_width)
        play = arcade.gui.UIFlatButton(text="GO!", width=self._button_width)

        stake = arcade.gui.UITextArea(text=str(int(self.stake)), width=c.MENU_SPACING)
        total = arcade.gui.UITextArea(text=str(int(self.money)), width=c.MENU_SPACING)

        self.grid.add(child=self.steps, column=0, row=1)
        self.grid.add(child=self.select, column=0, row=2)
        self.grid.add(child=self.money, column=0, row=0)
        self.anchor.add(anchor_y=c.Alignment.CENTER, anchor_x=c.Alignment.CENTER, child=self.grid)

        self.select.add(child=minus, column=0, row=0)
        self.select.add(child=plus, column=1, row=0)
        self.select.add(child=diff_easy, column=3, row=0)
        self.select.add(child=diff_mid, column=4, row=0)
        self.select.add(child=diff_hard, column=5, row=0)
        self.select.add(child=play, column=7, row=0)

