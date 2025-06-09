from __future__ import annotations

import logging
import typing

import arcade
import arcade.gui
import arcade.gui.experimental

import frontend.constants as c
from frontend.views.base import BaseGUI

if typing.TYPE_CHECKING:
    from frontend.window import MainWindow

logger = logging.getLogger(__name__)


class LobbysView(BaseGUI):
    def __init__(self, window: MainWindow, game_mode: c.GameModes) -> None:
        super().__init__(window=window)
        self._game_mode = game_mode
        self._button_width = (c.MENU_WIDTH - c.MENU_SPACING) / 2

        self.anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        self.box_layout = arcade.gui.UIBoxLayout()

        self.anchor.add(anchor_y=c.Alignment.CENTER, anchor_x=c.Alignment.CENTER, child=self.box_layout)
        self.box_layout.add(child=arcade.gui.UILabel(text="Test", font_size=c.MENU_FONT_SIZE))

        self.scroll = self.box_layout.add(child=arcade.gui.experimental.UIScrollArea())
        self.scroll.add(child=arcade.gui.UILabel(text="Test", font_size=c.MENU_FONT_SIZE))

    @property
    @typing.override
    def can_pause(self) -> bool:
        return True
