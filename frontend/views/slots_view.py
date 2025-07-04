from __future__ import annotations

import logging
import typing

import arcade
import arcade.gui
from arcade.gui import UILabel

import backend.main
from frontend.internal.decorator import add_event_listener
from frontend.internal.websocket_view import WebsocketView
from frontend.ui import Button
from frontend.ui import ButtonStyle
from shared.models import events

if typing.TYPE_CHECKING:
    import frontend.constants as c
    from frontend.window import MainWindow


class SlotsView(WebsocketView):
    def __init__(self, window: MainWindow, game_mode: c.GameModes, lobby_id: str) -> None:
        super().__init__(window, game_mode, lobby_id)
        '''erstellen der Grafischen Oberfläche'''
        self.ui = arcade.gui.UIManager()
        self.anchor = self.ui.add(arcade.gui.UIAnchorLayout(width=1000, height=500))
        self.box = self.anchor.add(arcade.gui.UIBoxLayout(height=500, width=1000))
        button = self.box.add(Button(text="Test", style=ButtonStyle()))
        button.set_handler("on_click", self.on_button_press)
        button = self.box.add(Button(text="turn", style=ButtonStyle()))
        button.set_handler( "on_click",self.on_button_press)

        ''''''

    def on_button_press(self, _: arcade.gui.UIOnClickEvent) -> None:
        self.send_event(events.StartSpin(einsatz=20))

    @typing.override
    def on_draw(self) -> bool | None:
        super().on_draw()
        self.ui.draw()

    @typing.override
    def on_show_view(self) -> None:
        self.ui.enable()

    @typing.override
    def on_hide_view(self) -> None:
        self.ui.disable()

