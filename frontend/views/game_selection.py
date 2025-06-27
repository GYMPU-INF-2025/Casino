from __future__ import annotations

import logging
import typing

import arcade
import arcade.gui
import arcade.gui.experimental
from arcade import color

import frontend.constants as c
from frontend import ui
from frontend.ui import BoxLayout
from frontend.ui import Button
from frontend.ui import ButtonStyle
from frontend.ui import Label
from frontend.views.base import BaseGUI

if typing.TYPE_CHECKING:
    from frontend.window import MainWindow
    from shared.models import responses

logger = logging.getLogger(__name__)


class GameSelectionView(BaseGUI):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window=window)
        self._button_width = (c.MENU_WIDTH - c.MENU_SPACING) / 2

        self.grid = arcade.gui.UIGridLayout(
            column_count=2, row_count=4, horizontal_spacing=c.MENU_SPACING, vertical_spacing=c.MENU_SPACING
        )
        self.anchor = self.ui.add(arcade.gui.UIAnchorLayout())


        button = []
        i = 0
        for attr in dir(c.GameModes.__members__):
                print(f"Property: {attr}")
                i += 1
                new_button = Button(text=attr)
                button.append(new_button)
                self.grid.add(new_button, column=1, row=i)





        self.error_text = arcade.gui.UILabel(
            text="", text_color=color.RED, width=c.MENU_WIDTH, align=c.Alignment.CENTER, font_size=c.MENU_FONT_SIZE - 10
        )
        self.grid.add(self.error_text, column=0, column_span=2, row=3)

        self.anchor.add(anchor_y=c.Alignment.CENTER, anchor_x=c.Alignment.CENTER, child=self.grid)