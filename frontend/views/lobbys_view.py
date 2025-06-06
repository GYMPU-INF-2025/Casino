from __future__ import annotations

import logging
import typing

import arcade
import arcade.gui
import arcade.gui.experimental

import frontend.constants as c
from frontend.net import ClientHTTPError
from frontend.views.base import BaseGUI
import arcade.color as color

if typing.TYPE_CHECKING:
    from frontend.window import MainWindow
    from arcade.types import Color

logger = logging.getLogger(__name__)


class LobbysView(BaseGUI):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window=window)

        self._button_width = (c.MENU_WIDTH - c.MENU_SPACING) / 2

        self.grid = arcade.gui.UIGridLayout(
            column_count=2, row_count=4, horizontal_spacing=c.MENU_SPACING, vertical_spacing=c.MENU_SPACING
        )
        self.anchor = self.ui.add(arcade.gui.UIAnchorLayout())


        self.anchor.add(anchor_y=c.Alignment.CENTER, anchor_x=c.Alignment.CENTER, child=self.grid)

    