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

        self.grid = arcade.gui.UIGridLayout(
            column_count=2, row_count=2, horizontal_spacing=c.MENU_SPACING, vertical_spacing=c.MENU_SPACING
        )
        self.anchor = self.ui.add(arcade.gui.UIAnchorLayout())