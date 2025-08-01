from __future__ import annotations

__all__ = ("MainWindow",)

import logging
import typing

import arcade
from arcade import View

import frontend.constants as c
from frontend.internal.net_client import NetClient
from frontend.net.rest_client import RestClient
from frontend.views import MainMenu
from frontend.views import PauseMenu
from frontend.views import TitleView
from frontend.views.blackjack_view import BlackjackView
from frontend.views.chickengame_view import ChickengameView
from frontend.views.game_selection import GameSelectionView
from frontend.views.lobbys_view import LobbysView
from frontend.views.login_view import LoginMenu
from frontend.views.mines_view import MinesView
from frontend.views.slots_view import SlotsView

if typing.TYPE_CHECKING:
    import pathlib

    from pyglet.event import EVENT_HANDLE_STATE

    from frontend.views.base import BaseView

logger = logging.getLogger(__name__)


class MainWindow(arcade.Window):
    """Main windows class storing the different views and managing what is being shown.

    Authors: Christopher
    """

    def __init__(self, root_path: pathlib.Path) -> None:
        logger.debug("Initializing Main Window")
        logger.debug("Screen size: %sx%s", c.SCREEN_WIDTH, c.SCREEN_HEIGHT)
        logger.debug("Center: %s,%s", c.CENTER_X, c.CENTER_Y)
        super().__init__(title=c.WINDOW_NAME, fullscreen=c.FULL_SCREEN, width=c.SCREEN_WIDTH, height=c.SCREEN_HEIGHT)
        arcade.set_background_color(arcade.color.BLACK)
        self.set_update_rate(1 / c.UPDATES_PER_SECOND)
        self.set_fps(c.DEFAULT_FPS)

        self.shader_path = root_path / "shaders"
        self.net_client = NetClient[RestClient](RestClient, "127.0.0.1:8000")

        self._title_view = TitleView(window=self)
        self._main_menu = MainMenu(window=self)
        self._pause_menu = PauseMenu(window=self)
        self._login_menu = LoginMenu(window=self)
        self._game_selection = GameSelectionView(window=self)

        self._blackjack_lobby_view = LobbysView(window=self, game_mode=c.GameModes.BLACKJACK)

        self._current_selected_view: BaseView = self._title_view
        self._show_view(self._title_view)

    def set_fps(self, fps: int) -> None:
        """Helper function to set the fps. If you try to set the fps higher than the update rate, it caps the fps
        to the update rate.

        Authors: Christopher
        """
        if fps > c.UPDATES_PER_SECOND:
            logger.debug(
                "Tried setting fps to %s, faster then the update rate of %s, capping fps to %s",
                fps,
                c.UPDATES_PER_SECOND,
                c.UPDATES_PER_SECOND,
            )
            fps = c.UPDATES_PER_SECOND
        self.set_draw_rate(1 / fps)

    def get_shader_path(self, shader_name: str) -> pathlib.Path:
        """Helper method to get the shader path."""
        return self.shader_path / f"{shader_name}.glsl"

    @typing.override
    def show_view(self, new_view: View) -> None:
        """Debug function that overrides the normal show_view function and adds debug logging.

        Authors: Christopher
        """
        logger.debug("Showing view %s", new_view)
        super().show_view(new_view)

    def _show_view(self, view: BaseView) -> None:
        """Helper function that calls activate/deactivate on views before showing/hiding them and stores the current
        view in `_current_selected_view`. This is used to draw the background when opening the pause menu.

        Authors: Christopher
        """
        if self.current_view == view:
            return
        self._current_selected_view.deactivate()
        self.show_view(view)
        self._current_selected_view = view
        self._current_selected_view.activate()

    def show_main_menu(self) -> None:
        """Function that shows the main menu, if the user is authenticated, if not it shows the login menu.

        Authors: Christopher
        """
        if self.net_client.authorized:
            self._show_view(self._main_menu)
        else:
            self._show_view(self._login_menu)

    def show_game(self, game_mode: c.GameModes, lobby_id: str) -> None:
        """Function called to show a view for a game.
        It takes the game mode and the lobby id to create the game view.

        Authors: Christopher
        """
        match game_mode:
            case c.GameModes.BLACKJACK:
                self._show_view(BlackjackView(window=self, game_mode=game_mode, lobby_id=lobby_id))
            case c.GameModes.CHICKENGAME:
                self._show_view(ChickengameView(window=self, game_mode=game_mode, lobby_id=lobby_id))
            case c.GameModes.MINES:
                self._show_view(MinesView(window=self, game_mode=game_mode, lobby_id=lobby_id))
            case c.GameModes.SLOTS:
                self._show_view(SlotsView(window=self, game_mode=game_mode, lobby_id=lobby_id))
            case _:
                raise TypeError(f"No game view for game mode: {game_mode}")

    def show_game_selection(self) -> None:
        """Function that shows the game selection view.

        Authors: Christopher
        """
        self._show_view(view=self._game_selection)

    def show_lobbys(self, game_mode: c.GameModes) -> None:
        """Function that shows the lobby selection view for different games.

        Authors: Christopher
        """
        match game_mode:
            case c.GameModes.BLACKJACK:
                self._show_view(self._blackjack_lobby_view)
            case _:
                raise TypeError(f"No lobbys view for game mode: {game_mode}")

    def toggle_pause_menu(self) -> None:
        """Function that toggles the pause menu.

        Authors: Christopher
        """
        if self.current_view == self._pause_menu:
            self.show_view(self._current_selected_view)
        else:
            self.show_view(self._pause_menu)

    @typing.override
    def on_key_press(self, symbol: int, modifiers: int) -> EVENT_HANDLE_STATE:
        """Listener to key presses, if the user presses escape and the current view allows pausing, it shows the
        pause menu.

        Authors: Christopher
        """
        if symbol == arcade.key.ESCAPE and self._current_selected_view.can_pause:
            self.toggle_pause_menu()

    @property
    def current_selected_view(self) -> BaseView:
        return self._current_selected_view

    @typing.override
    def on_update(self, delta_time: float) -> bool | None:
        """On update function that checks if the user is logged in and if not it shows the login screen.

        Authors: Christopher
        """
        if not self.net_client.authorized and self.current_selected_view != self._title_view:
            self._show_view(self._login_menu)
