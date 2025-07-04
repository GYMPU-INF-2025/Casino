from __future__ import annotations

import logging
import typing

import arcade
import arcade.gui
import arcade.gui.experimental

import frontend.constants as c
from frontend.ui import Button
from frontend.views.base import BaseGUI

if typing.TYPE_CHECKING:
    from collections.abc import Callable

    from frontend.window import MainWindow

logger = logging.getLogger(__name__)


class GameSelectionView(BaseGUI):
    """View that allows selecting the game mode.

    The buttons for each game are autopopulated for every element in the
    `GameModes` enum.

    Authors: Quirin, Christopher
    """

    def __init__(self, window: MainWindow) -> None:
        super().__init__(window=window)

        self.anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        self.box = self.anchor.add(arcade.gui.UIBoxLayout(space_between=c.MENU_SPACING))

        for attr in c.GameModes:
            new_button = Button(text=attr.value.capitalize(), width=c.MENU_WIDTH)
            self.box.add(new_button)
            new_button.set_handler("on_click", self.button_callback(attr))

    def button_callback(self, game_mode: c.GameModes) -> Callable[[arcade.gui.UIOnClickEvent], None]:
        """Callback function that shows the lobby view for the wanted game mode."""

        def inner_callback(_: arcade.gui.UIOnClickEvent) -> None:
            self.window.show_lobbys(game_mode)

        return inner_callback

    @property
    @typing.override
    def can_pause(self) -> bool:
        return True
