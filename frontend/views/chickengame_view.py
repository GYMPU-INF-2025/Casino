from __future__ import annotations

import logging
import typing

import arcade
import arcade.gui
import websocket
from arcade.gui import UIAnchorLayout, events
from arcade.gui.widgets.buttons import UITextureButton

from backend.internal.ws import add_event_listener
from frontend.constants import SCREEN_HEIGHT, SCREEN_WIDTH, Alignment, GameModes
from frontend.internal.websocket_view import WebsocketView
from frontend.views.base import BaseGUI
from shared.models import events

if typing.TYPE_CHECKING:
    from frontend.window import MainWindow
    from shared.models import responses, requests

logger = logging.getLogger(__name__)


class ChickengameView(WebsocketView):
    def __init__(self, window: MainWindow, game_mode: GameModes, lobby_id: str) -> None:
        super().__init__(window=window, game_mode=game_mode, lobby_id=lobby_id)
        self.ui = arcade.gui.UIManager()

        self._button_width = SCREEN_WIDTH / 6
        self._button_height = SCREEN_HEIGHT / 6
        self._steps_width = SCREEN_WIDTH / 10
        self._steps_height = (SCREEN_HEIGHT / 3) * 2

        self.gamemode = 0
        self.gamemode_list = ['Easy', 'Medium', 'Hard']
        self.stake = 0
        self.total = 650
        self.take = 0

        self.img = arcade.load_texture('assets/chickengame/img.png')
        self.button_img = arcade.load_texture('assets/chickengame/button.png')
        self.street_img = arcade.load_texture('assets/chickengame/street.png')

        self.create_grids()
        self.show_money()
        self.show_steps()
        self.show_buttons()

    def create_grids(self) -> None:
        def make_grid(column_count, row_count, height):
            return arcade.gui.UIGridLayout(
                column_count=column_count,
                row_count=row_count,
                row_height=height,
                size_hint=(None, None),
                width=SCREEN_WIDTH,
                height=height,
            )

        self.grid_top = make_grid(3, 1, self._button_height)
        self.grid_mid = make_grid(10, 1, self._steps_height)
        self.grid_bottom = make_grid(7, 1, self._button_height)

        self.anchor_top = self.ui.add(UIAnchorLayout())
        self.anchor_mid = self.ui.add(UIAnchorLayout())
        self.anchor_bottom = self.ui.add(UIAnchorLayout())

        self.anchor_top.add(anchor_y=Alignment.TOP, anchor_x=Alignment.CENTER, child=self.grid_top)
        self.anchor_mid.add(anchor_y=Alignment.CENTER, anchor_x=Alignment.CENTER, child=self.grid_mid)
        self.anchor_bottom.add(anchor_y=Alignment.BOTTOM, anchor_x=Alignment.CENTER, child=self.grid_bottom)

    def show_money(self) -> None:
        def make_label(text: str) -> arcade.gui.UILabel:
            return arcade.gui.UILabel(
                text=text,
                width=SCREEN_WIDTH / 3,
                height=self._button_height,
                font_size=50,
                align=Alignment.CENTER,
            )

        self.stake_label = make_label(f'Stake: {int(self.stake)}')
        self.gamemode_label = make_label(f'Gamemode: {self.gamemode_list[self.gamemode]}')
        self.total_label = make_label(f'Money: {int(self.total)}')

        for i, label in enumerate([self.stake_label, self.gamemode_label, self.total_label]):
            anchor = UIAnchorLayout(width=SCREEN_WIDTH / 3, height=self._button_height)
            anchor.add(child=label, anchor_x="center", anchor_y="center")
            self.grid_top.add(child=anchor, column=i, row=0)

    def show_steps(self) -> None:
        self.steps = [
            UITextureButton(texture=self.img, width=self._steps_width, height=self._steps_height)
            for _ in range(self.grid_mid.column_count)
        ]

        street_texture = arcade.load_texture('assets/chickengame/street.png')
        self.street_img = arcade.gui.UIImage(texture=street_texture)
        self.anchor_mid.add(child=self.street_img, anchor_x="center", anchor_y="center", index=0)

        for i, step in enumerate(self.steps):
            step.text = str(i)
            self.grid_mid.add(child=step, column=i, row=0)

            @add_event_listener(events.UpdateStep)
            @step.event("on_click")
            def on_click(event: events.UpdateStep, index=i):
                self.steps[index].texture = self.show_alive_img()
                self.steps[index].texture_hovered = self.show_alive_img()
                self.steps[index].texture_pressed = self.show_alive_img()
                self.on_draw()

    def show_buttons(self) -> None:
        def make_button(text: str, callback) -> UITextureButton:
            button = UITextureButton(
                texture=self.button_img,
                text=text,
                width=self._button_width,
                height=self._button_height,
            )

            @button.event("on_click")
            def handle_click(_: arcade.gui.UIOnClickEvent) -> None:
                callback()
            return button

        self.minus_button = make_button("-100", self.decrease_stake)
        self.plus_button = make_button("+100", self.increase_stake)
        self.diff_easy_button = make_button("Easy", lambda: self.set_gamemode(0, events.UpdateGamemode))
        self.diff_mid_button = make_button("Medium", lambda: self.set_gamemode(1, events.UpdateGamemode))
        self.diff_hard_button = make_button("Hard", lambda: self.set_gamemode(2, events.UpdateGamemode))
        self.take_button = make_button(f"Take: {self.take}", self.refresh)

        for index, button in enumerate([
            self.minus_button, self.plus_button,
            self.diff_easy_button, self.diff_mid_button, self.diff_hard_button,
            self.take_button
        ]):
            self.grid_bottom.add(child=button, column=index, row=0)

    @add_event_listener(events.UpdateTake)
    def decrease_stake(self, event: events.UpdateTake) -> None:
        if self.stake >= 100:
            self.stake -= 100
            self.total += 100
        self.refresh()

    @add_event_listener(events.UpdateTake)
    def increase_stake(self, event: events.UpdateTake) -> None:
        if self.total >= 100:
            self.total -= 100
            self.stake += 100
        self.refresh()

    @add_event_listener(events.UpdateGamemode)
    def set_gamemode(self, mode: int, event: events.UpdateGamemode) -> None:
        event.gamemode = mode
        self.gamemode = mode
        self.refresh()

    def refresh(self) -> None:
        self.stake_label.text = f'Stake: {self.stake}'
        self.gamemode_label.text = f'Gamemode: {self.gamemode_list[self.gamemode]}'
        self.total_label.text = f'Money: {int(self.total)}'
        self.take_button.text = f"Take: {self.take}"

    def clear_grids(self) -> None:
        self.grid_top.clear()
        self.grid_mid.clear()
        self.grid_bottom.clear()

    def show_alive_img(self) -> arcade.Texture:
        return arcade.load_texture('assets/chickengame/alive_img.png')

    def show_dead_img(self) -> arcade.Texture:
        return arcade.load_texture('assets/chickengame/dead_img.png')

    @property
    @typing.override
    def can_pause(self) -> bool:
        return True

    def on_draw(self) -> None:
        super().on_draw()
        self.ui.draw()

    def on_show_view(self) -> None:
        self.ui.enable()

    def on_hide_view(self) -> None:
        self.ui.disable()