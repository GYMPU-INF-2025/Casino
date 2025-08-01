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

if typing.TYPE_CHECKING:
    import collections.abc

    from frontend.window import MainWindow
    from shared.models import responses

logger = logging.getLogger(__name__)

T = typing.TypeVar("T")


def try_get(iterable: collections.abc.Sequence[T], index: int) -> T | None:
    try:
        return iterable[index]
    except IndexError:
        return None


class LobbysView(BaseGUI):
    """View that shows every available lobby for a game mode and lets you pick & join a lobby.

    Authors: Christopher
    """

    def __init__(self, window: MainWindow, game_mode: c.GameModes) -> None:
        super().__init__(window=window)
        self._game_mode = game_mode
        self._button_width = (c.MENU_WIDTH - c.MENU_SPACING) / 2

        self._lobbys: list[responses.PublicGameLobby] = []
        self._selected: int | None = None

        self.anchor = self.ui.add(arcade.gui.UIAnchorLayout())
        self.box_layout = self.anchor.add(
            arcade.gui.UIBoxLayout(align=c.Alignment.TOP, width=1000, height=900, space_between=20)
        )
        self.box_layout.add(child=arcade.gui.UILabel(text="Lobbys", font_size=50))
        self._lobbys_list = self.box_layout.add(child=BoxLayout(size_hint_min=(1000, 500)))
        self._lobbys_list.with_background(color=Color(0, 0, 0, 100))
        control_buttons = self.box_layout.add(
            child=BoxLayout(space_between=20, align=c.Alignment.RIGHT, vertical=False, size_hint_min=(1000, 50))
        )
        self._join_button = control_buttons.add(Button(text="Join lobby", style=ButtonStyle(), width=200))
        self._join_button.set_handler("on_click", self.on_lobby_join_press)
        control_buttons.add(Button(text="Create new lobby", style=ButtonStyle(), width=300)).set_handler(
            "on_click", self.on_lobby_create_press
        )
        control_buttons.add(Button(text="Refresh", style=ButtonStyle(), width=170)).set_handler(
            "on_click", lambda _: self.refresh_lobbys()
        )
        self._time_since_refresh = 0
        self.refresh_ui()

    def on_lobby_join_press(self, _: arcade.gui.UIOnClickEvent) -> None:
        """Callback for the join lobby button."""
        if self._selected is None:
            return
        lobby_label = self._lobbys_list.children[self._selected].children[1]
        if not isinstance(lobby_label, Label):
            return
        lobby_id = lobby_label.text
        logger.debug("Trying to connect to lobby with id: %s", lobby_id)
        self.window.show_game(self._game_mode, lobby_id=lobby_id)

    def on_lobby_create_press(self, _: arcade.gui.UIOnClickEvent) -> None:
        """Callback for the create lobby button"""
        self.window.net_client.rest.create_lobby(self._game_mode.value)
        self.refresh_lobbys()

    def refresh_ui(self) -> None:
        """Function that refreshes the ui. This recreates every lobby row in the container.

        This does not fetch/update the lobbys from the backend!
        """
        self._lobbys_list.clear()
        self._add_lobbys_row("Game", "Lobby code", "Players")
        self.show_border(row_num=0)
        for i, lobby in enumerate(self._lobbys):
            self.add_lobby(lobby_code=lobby.id, max_players=lobby.max_clients, num_players=lobby.num_clients)
            if self._selected is not None and i + 1 == self._selected:
                self.show_border(self._selected)
        if len(self._lobbys) == 0:
            self._lobbys_list.add(child=arcade.gui.UILabel(text="No lobbys found!", font_size=c.MENU_FONT_SIZE))

    def refresh_lobbys(self) -> None:
        """Function that fetches new lobbys from the backend and refreshes the ui after that.

        It saves the current selected lobby id, so that the _selected attribute can be correctly set again.
        """
        selected_lobby_id = self._lobbys[self._selected - 1].id if self._selected else None
        self._lobbys = self.window.net_client.rest.get_lobbys(game=self._game_mode.value)
        self._time_since_refresh = 0
        if selected_lobby_id:
            for i, lobby in enumerate(self._lobbys):
                if lobby.id == selected_lobby_id and not lobby.full:
                    self._selected = i + 1
                    break
                if lobby.id == selected_lobby_id and lobby.full:
                    self._selected = None
                    break
                if i == len(self._lobbys) - 1:
                    self._selected = None
        self.refresh_ui()

    def add_lobby(self, lobby_code: str, max_players: int, num_players: int) -> None:
        """This function adds a new lobby row."""
        self._add_lobbys_row(self._game_mode.value.title(), lobby_code, f"{num_players}/{max_players} Players")

    def _add_lobbys_row(self, colum_1: str, colum_2: str, colum_3: str) -> None:
        """This function adds a row to the `_lobbys_list` container. Each row is a grid with 3 columns."""
        grid = arcade.gui.UIGridLayout(row_count=1, column_count=3, width=1200)
        grid.add(child=Label(text=colum_1, font_size=c.MENU_FONT_SIZE), column=0, row=0).set_min_size_x(400)
        grid.add(child=Label(text=colum_2, font_size=c.MENU_FONT_SIZE), column=1, row=0).set_min_size_x(300)
        grid.add(child=Label(text=colum_3, font_size=c.MENU_FONT_SIZE), column=2, row=0).set_min_size_x(300)
        self._lobbys_list.add(child=grid)

    def show_border(self, row_num: int, width: int = 3, color: Color | None = None) -> None:
        """Adds a border to a children in the `_lobbys_list` container."""
        if color is None:
            color = Color(255, 255, 255)
        self._lobbys_list.children[row_num].with_border(width=width, color=color)

    def hide_border(self, row_num: int) -> None:
        """Removes a border from a children in the `_lobbys_list` container."""
        self._lobbys_list.children[row_num].with_border(width=0)

    @typing.override
    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
        """This callback is used to create the hover animation, when hovering above a lobby row.

        The hover effect adds a border to the row that your mouse cursor is on. Lobbys that are full
        will not get a hover effect, because they cant be selected.
        """
        for i, row in enumerate(self._lobbys_list.children):
            if i == 0 or not isinstance(row, arcade.gui.UIGridLayout):
                continue

            if row.rect.point_in_rect(point=(x, y)):
                if (lobby := try_get(self._lobbys, i - 1)) and lobby.full:
                    self.hide_border(row_num=i)
                    continue
                self.show_border(row_num=i)
            elif i != self._selected:
                self.hide_border(row_num=i)

    @typing.override
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        """This callback is used to select a lobby row when clicking on it. Full lobbys are ignored."""
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        for i, row in enumerate(self._lobbys_list.children):
            if i == 0 or not isinstance(row, arcade.gui.UIGridLayout):
                continue

            if not row.rect.point_in_rect(point=(x, y)):
                continue

            if self._selected == i:
                self.hide_border(row_num=i)
                self._selected = None
            elif (lobby := try_get(self._lobbys, i - 1)) and lobby.full:
                return
            else:
                if self._selected is not None:
                    self.hide_border(row_num=self._selected)
                self.show_border(row_num=i)
                self._selected = i

    @typing.override
    def on_update(self, delta_time: float) -> None:
        self._join_button.disabled = self._selected is None
        self._time_since_refresh += delta_time
        if self._time_since_refresh >= c.LOBBY_REFRESH_SECONDS:
            self.refresh_lobbys()
            # TODO: Check if this works

    @typing.override
    def on_show_view(self) -> None:
        self.refresh_lobbys()
        self.ui.enable()

    @property
    @typing.override
    def can_pause(self) -> bool:
        return True

    @typing.override
    def deactivate(self) -> None:
        self._selected = None
