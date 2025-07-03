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
    from frontend.window import MainWindow
    from shared.models import responses

logger = logging.getLogger(__name__)


class LobbysView(BaseGUI):
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
        self.refresh_ui()

    def on_lobby_join_press(self, _: arcade.gui.UIOnClickEvent) -> None:
        if self._selected is None:
            return
        lobby_label = self._lobbys_list.children[self._selected].children[1]
        if not isinstance(lobby_label, Label):
            return
        lobby_id = lobby_label.text
        logger.debug("Trying to connect to lobby with id: %s", lobby_id)
        self.window.show_game(self._game_mode, lobby_id=lobby_id)

    def on_lobby_create_press(self, _: arcade.gui.UIOnClickEvent) -> None:
        self.window.net_client.rest.create_lobby(self._game_mode.value)
        self.refresh_lobbys()

    def refresh_ui(self) -> None:
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
        selected_lobby_id = self._lobbys[self._selected - 1].id if self._selected else None
        self._lobbys = self.window.net_client.rest.get_lobbys(game=self._game_mode.value)
        if selected_lobby_id:
            for i, lobby in enumerate(self._lobbys):
                if lobby.id == selected_lobby_id:
                    self._selected = i + 1
                    break
                if i == len(self._lobbys) - 1:
                    self._selected = None
        self.refresh_ui()

    def add_lobby(self, lobby_code: str, max_players: int, num_players: int) -> None:
        self._add_lobbys_row(self._game_mode.value.title(), lobby_code, f"{num_players}/{max_players} Players")

    def _add_lobbys_row(self, colum_1: str, colum_2: str, colum_3: str) -> None:
        grid = arcade.gui.UIGridLayout(row_count=1, column_count=3, width=1200)
        grid.add(child=Label(text=colum_1, font_size=c.MENU_FONT_SIZE), column=0, row=0).set_min_size_x(400)
        grid.add(child=Label(text=colum_2, font_size=c.MENU_FONT_SIZE), column=1, row=0).set_min_size_x(300)
        grid.add(child=Label(text=colum_3, font_size=c.MENU_FONT_SIZE), column=2, row=0).set_min_size_x(300)
        self._lobbys_list.add(child=grid)

    def show_border(self, row_num: int, width: int = 3, color: Color | None = None) -> None:
        if color is None:
            color = Color(255, 255, 255)
        self._lobbys_list.children[row_num].with_border(width=width, color=color)

    def hide_border(self, row_num: int) -> None:
        self._lobbys_list.children[row_num].with_border(width=0)

    @typing.override
    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
        for i, row in enumerate(self._lobbys_list.children):
            if i == 0 or not isinstance(row, arcade.gui.UIGridLayout):
                continue

            if row.rect.point_in_rect(point=(x, y)):
                self.show_border(row_num=i)
            elif i != self._selected:
                self.hide_border(row_num=i)

    @typing.override
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
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
            else:
                if self._selected is not None:
                    self.hide_border(row_num=self._selected)
                self.show_border(row_num=i)
                self._selected = i

    @typing.override
    def on_update(self, delta_time: float) -> None:
        self._join_button.disabled = self._selected is None

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
