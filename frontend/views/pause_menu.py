from __future__ import annotations

__all__ = ("PauseMenu",)

import logging
import typing

import arcade
import arcade.gui

import frontend.constants as c
from frontend.views.base import BaseView

if typing.TYPE_CHECKING:
    from arcade.types import Color

    from frontend.window import MainWindow


logger = logging.getLogger(__name__)


class PauseMenu(BaseView):
    def __init__(self, window: MainWindow, background_color: Color | None = None) -> None:
        super().__init__(window=window, background_color=background_color)
        self.shown = False
        self.manager = arcade.gui.UIManager()

        self._spacing = 20
        self._menu_width = 400
        self._button_width = (self._menu_width - self._spacing) / 2

        self.grid = arcade.gui.UIGridLayout(
            column_count=2, row_count=3, horizontal_spacing=self._spacing, vertical_spacing=self._spacing
        )
        self.anchor = self.manager.add(arcade.gui.UIAnchorLayout())
        self.setup()
        self.anchor.add(anchor_y=c.Alignment.CENTER, anchor_x=c.Alignment.CENTER, child=self.grid)

    def setup(self) -> None:
        close_menu_button = arcade.gui.UIFlatButton(text="Close Menu", width=self._menu_width)
        close_game_button = arcade.gui.UIFlatButton(text="Close Game", width=self._menu_width)

        @close_menu_button.event("on_click")
        def on_close_menu_button(_: arcade.gui.UIOnClickEvent) -> None:
            self.window.toggle_pause_menu()

        @close_game_button.event("on_click")
        def on_close_game_button(_: arcade.gui.UIOnClickEvent) -> None:
            arcade.exit()

        self.grid.add(child=close_menu_button, column=0, row=0, column_span=2)
        self.grid.add(child=close_game_button, column=0, row=1, column_span=2)

    @typing.override
    def on_draw(self) -> bool | None:
        self.clear()
        self.manager.draw()

    @typing.override
    def on_show_view(self) -> None:
        self.manager.enable()

    @typing.override
    def on_hide_view(self) -> None:
        self.manager.disable()
