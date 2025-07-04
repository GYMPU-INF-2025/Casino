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

        self.anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        self.box = self.anchor.add(arcade.gui.UIBoxLayout(space_between=c.MENU_SPACING))

        for attr in c.GameModes:
            new_button = Button(text=attr.value.capitalize(), width=c.MENU_WIDTH)
            self.box.add(new_button)
            new_button.set_handler("on_click", self.button_callback(attr))

    def button_callback(self, gameMode: c.GameModes):
        def inner_callback(_: arcade.gui.UIOnClickEvent) -> None:
            self.window.show_lobbys(gameMode)

        return inner_callback

    def can_pause(self) -> bool:
        return True