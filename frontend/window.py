from __future__ import annotations

__all__ = ("MainWindow",)

import logging
import pathlib
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
    def __init__(self, root_path: pathlib.Path) -> None:
        logger.debug("Initializing Main Window")
        super().__init__(title=c.WINDOW_NAME, fullscreen=c.FULL_SCREEN, width=c.SCREEN_WIDTH, height=c.SCREEN_HEIGHT)
        arcade.set_background_color(arcade.color.BLACK)
        self.set_update_rate(c.UPDATE_RATE)
        self.set_fps(c.DEFAULT_FPS)

        self.shader_path = root_path / "shaders"

        self._title_view = TitleView(window=self, background_color=arcade.color.BLACK)
        self._main_menu = MainMenu(window=self, background_color=arcade.color.YELLOW)
        self._pause_menu = PauseMenu(window=self)

        self._current_selected_view: BaseView = self._title_view
        self._show_view(self._title_view)
    
    def set_fps(self, fps: int) -> None:
        _fps = 1/fps
        if _fps > c.UPDATE_RATE:
            _fps = c.UPDATE_RATE
        self.set_draw_rate(_fps)

    def get_shader_path(self, shader_name: str) -> pathlib.Path:
        return self.shader_path / f"{shader_name}.glsl"

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
        if symbol == arcade.key.ESCAPE and self._current_selected_view.can_pause:
            self.toggle_pause_menu()

    @property
    def current_selected_view(self) -> BaseView:
        return self._current_selected_view
