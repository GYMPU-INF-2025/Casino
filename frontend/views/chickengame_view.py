from __future__ import annotations

import logging
import typing
from tkinter.constants import CENTER

import arcade
import arcade.gui
import arcade.gui.experimental
from PIL.ImageQt import align8to32
from arcade.gui import events
from arcade.types import Color
from pyglet import image
from pyglet.resource import texture

import frontend.constants as c
from backend.internal.ws import WebsocketClient
from frontend.constants import SCREEN_HEIGHT
from frontend.internal.websocket_view import WebsocketView
from frontend.ui import BoxLayout
from frontend.ui import Button
from frontend.ui import ButtonStyle
from frontend.ui import Label
from frontend.views.base import BaseGUI


from frontend.views.base import BaseGUI

if typing.TYPE_CHECKING:
    from frontend.window import MainWindow
    from shared.models import responses, requests

logger = logging.getLogger(__name__)


class ChickengameView(WebsocketView, BaseGUI):
    def __init__(self, window: MainWindow, game_mode: c.GameModes) -> None:
        super().__init__(window=window)

        self._button_width = c.SCREEN_WIDTH / 6
        self._steps_width = c.SCREEN_WIDTH / 10
        self._steps_height = (c.SCREEN_HEIGHT / 3)*2

        self.stake = 0
        self.gamemode = 0
        self.gamemode_list = ['Easy', 'Medium', 'Hard']
        self.total = 650

        self.img = arcade.load_texture('assets/background.png')

        self.grid_top = arcade.gui.UIGridLayout(
            column_count=3, row_count=1, row_height=c.SCREEN_HEIGHT/6
        )
        self.grid_mid = arcade.gui.UIGridLayout(
            column_count=10, row_count=1, row_height=self._steps_height
        )
        self.grid_bottom = arcade.gui.UIGridLayout(
            column_count=6, row_count=1, row_height=c.SCREEN_HEIGHT/6
        )

        self.anchor_top = self.ui.add(arcade.gui.UIAnchorLayout())
        self.anchor_mid = self.ui.add(arcade.gui.UIAnchorLayout())
        self.anchor_bottom = self.ui.add(arcade.gui.UIAnchorLayout())

        self.show_money()

        self.show_steps()

        minus_button = arcade.gui.UIFlatButton(text="-100", width=self._button_width, height=SCREEN_HEIGHT/6)
        plus_button = arcade.gui.UIFlatButton(text="+100", width=self._button_width, height=SCREEN_HEIGHT/6)
        diff_easy_button = arcade.gui.UIFlatButton(text="Easy", width=self._button_width, height=SCREEN_HEIGHT/6)
        diff_mid_button = arcade.gui.UIFlatButton(text="Medium", width=self._button_width, height=SCREEN_HEIGHT/6)
        diff_hard_button = arcade.gui.UIFlatButton(text="Hard", width=self._button_width, height=SCREEN_HEIGHT/6)
        play_button = arcade.gui.UIFlatButton(text="GO!", width=self._button_width, height=SCREEN_HEIGHT/6)

        @minus_button.event("on_click")
        def on_minus_button(_: arcade.gui.UIOnClickEvent) -> None:
            if not self.stake < 100 :
                self.stake -= 100
                self.total += 100
                self.refresh()

        @plus_button.event("on_click")
        def on_plus_button(_: arcade.gui.UIOnClickEvent) -> None:
            if not self.total < 100:
                self.total -= 100
                self.stake += 100
                self.refresh()

        @diff_easy_button.event("on_click")
        def on_diff_easy_button(_: arcade.gui.UIOnClickEvent) -> None:
            self.gamemode = 0
            self.refresh()

        @diff_mid_button.event("on_click")
        def on_diff_mid_button(_: arcade.gui.UIOnClickEvent) -> None:
            self.gamemode = 1
            self.refresh()

        @diff_hard_button.event("on_click")
        def on_diff_hard_button(_: arcade.gui.UIOnClickEvent) -> None:
            self.gamemode = 2
            self.refresh()

        @play_button.event("on_click")
        def on_play_button(_: arcade.gui.UIOnClickEvent) -> None:
            self.refresh()

        self.anchor_top.add(anchor_y=c.Alignment.TOP, anchor_x=c.Alignment.LEFT, child=self.grid_top)
        self.anchor_mid.add(anchor_y=c.Alignment.CENTER, anchor_x=c.Alignment.LEFT, child=self.grid_mid)
        self.anchor_bottom.add(anchor_y=c.Alignment.BOTTOM, anchor_x=c.Alignment.LEFT, child=self.grid_bottom)

        self.grid_bottom.add(child=minus_button, column=0, row=0)
        self.grid_bottom.add(child=plus_button, column=1, row=0)
        self.grid_bottom.add(child=diff_easy_button, column=2, row=0)
        self.grid_bottom.add(child=diff_mid_button, column=3, row=0)
        self.grid_bottom.add(child=diff_hard_button, column=4, row=0)
        self.grid_bottom.add(child=play_button, column=5, row=0)

    @property
    @typing.override
    def can_pause(self) -> bool:
        return True

    def refresh(self) -> None:
        self.show_money()
        self.show_steps()

    def show_money(self) -> None:
        stake_textbox = arcade.gui.UITextArea(text='Stake: ' + str(int(self.stake)), width=c.SCREEN_WIDTH / 3,
                                                   height=c.SCREEN_HEIGHT / 6, font_size=c.SCREEN_HEIGHT / 22)
        gamemode_textbox = arcade.gui.UITextArea(text='Gamemode: ' + str(self.gamemode_list[self.gamemode]), width=c.SCREEN_WIDTH / 3,
                                                 height=c.SCREEN_HEIGHT / 6, font_size=c.SCREEN_HEIGHT / 22)
        total_textbox = arcade.gui.UITextArea(text='Money: ' + str(int(self.total)), width=c.SCREEN_WIDTH / 3,
                                                   height=c.SCREEN_HEIGHT / 6, font_size=c.SCREEN_HEIGHT / 22)
        self.grid_top.clear()
        self.grid_top.add(child=stake_textbox, column=0, row=0)
        self.grid_top.add(child=gamemode_textbox, column=1, row=0)
        self.grid_top.add(child=total_textbox, column=2, row=0)

    def show_steps(self) -> None:

        steps = [arcade.gui.UIImage(texture=self.img, width=self._steps_width, height=self._steps_height, ) for _ in
                 range(self.grid_mid.column_count)]

        for i, step in enumerate(steps):
            self.grid_mid.add(child=step, column=i, row=0)

    '''def show_alive_img(self) -> None:
        img = arcade.load_texture('assets/chickengame/alive_img.png')
        
    def show_dead_img(self) -> None:
        img = arcade.load_texture('assets/chickengame/dead_img.png')
        
    def show_done_img(self) -> None:
        img = arcade.load_texture('assets/chickengame/done.png')'''