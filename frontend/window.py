from __future__ import annotations

__all__ = ("MainWindow",)

import logging
import typing

import arcade
from arcade import View

import frontend.constants as c
from frontend.views import MainMenu
from frontend.views import PauseMenu
from frontend.views import TitleView

if typing.TYPE_CHECKING:
    from pyglet.event import EVENT_HANDLE_STATE

    from frontend.views.base import BaseView

logger = logging.getLogger(__name__)


class MainWindow(arcade.Window):
    def __init__(self) -> None:
        logger.debug("Initializing Main Window")
        super().__init__(title=c.WINDOW_NAME, fullscreen=c.FULL_SCREEN, width=c.SCREEN_WIDTH, height=c.SCREEN_HEIGHT)
        arcade.set_background_color(arcade.color.BLACK)

        self._title_view = TitleView(window=self, background_color=arcade.color.BLACK)
        self._main_menu = MainMenu(window=self, background_color=arcade.color.BLACK)
        self._pause_menu = PauseMenu(window=self, background_color=arcade.color.DARK_BLUE_GRAY)

        self._current_selected_view: BaseView = self._title_view
        self._show_view(self._title_view)

    @typing.override
    def show_view(self, new_view: View) -> None:
        logger.debug("Showing view %s", new_view)
        super().show_view(new_view)

    def _show_view(self, view: BaseView) -> None:
        self.show_view(view)
        self._current_selected_view = view

    def show_main_menu(self) -> None:
        self._show_view(self._main_menu)

    def toggle_pause_menu(self) -> None:
        if self._pause_menu.shown:
            self.show_view(self._current_selected_view)
            self._pause_menu.shown = False
        else:
            self.show_view(self._pause_menu)
            self._pause_menu.shown = True

    @typing.override
    def on_key_press(self, symbol: int, modifiers: int) -> EVENT_HANDLE_STATE:
        if symbol == arcade.key.ESCAPE:
            self.toggle_pause_menu()
