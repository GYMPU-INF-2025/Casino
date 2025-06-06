from __future__ import annotations

__all__ = ("MainMenu",)

import typing

import arcade
import arcade.gui

import frontend.constants as c
from frontend.views.base import BaseGUI

if typing.TYPE_CHECKING:
    from arcade.types import Color

    from frontend.window import MainWindow


class MainMenu(BaseGUI):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window=window)

        self._button_width = (c.MENU_WIDTH - c.MENU_SPACING) / 2

        self.grid = arcade.gui.UIGridLayout(
            column_count=2, row_count=3, horizontal_spacing=c.MENU_SPACING, vertical_spacing=c.MENU_SPACING
        )
        self.anchor = self.ui.add(arcade.gui.UIAnchorLayout())

        play_button = arcade.gui.UIFlatButton(text="Play", width=c.MENU_WIDTH)
        close_game_button = arcade.gui.UIFlatButton(text="Quit Game", width=self._button_width)
        logout_button = arcade.gui.UIFlatButton(text="Logout", width=self._button_width)
        profile_button = arcade.gui.UIFlatButton(text="Profile", width=self._button_width)
        options_button = arcade.gui.UIFlatButton(text="Options", width=self._button_width)

        @close_game_button.event("on_click")
        def on_close_game_button(_: arcade.gui.UIOnClickEvent) -> None:
            arcade.exit()
        
        @logout_button.event("on_click")
        def on_logout_button(_: arcade.gui.UIOnClickEvent) -> None:
            self.window.net_client.logout()
        
        self.grid.add(child=play_button, column=0, row=0, column_span=2)
        self.grid.add(child=logout_button, column=0, row=1)
        self.grid.add(child=profile_button, column=1, row=1)
        self.grid.add(child=options_button, column=0, row=2)
        self.grid.add(child=close_game_button, column=1, row=2)
        self.anchor.add(anchor_y=c.Alignment.CENTER, anchor_x=c.Alignment.CENTER, child=self.grid)

    @property
    @typing.override
    def can_pause(self) -> bool:
        return True