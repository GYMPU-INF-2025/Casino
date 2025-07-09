from __future__ import annotations

import logging
import random
import threading
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

        self.message_label = arcade.gui.UILabel(
            text="",
            text_color=arcade.color.RED,
            font_size=20,
            width=400,
            height=40,

        )
        self.message_Label.visible=False
        self.box.add(self.message_label.with_space_around(bottom=10))
        ''''''

    def on_button_press(self, _: arcade.gui.UIOnClickEvent) -> None:
        self.send_event(events.StartSpin(einsatz=20))

    def button2_on_press(self, _: arcade.gui.UIOnClickEvent) -> None:

    def kein_Geld(self, _: arcade.gui.UIOnClickEvent) -> None:
        self.message_Label.visible.text ="Nicht genug Geld!"
        self.message_Label.visible=True
        def hide():
            self.message_Label.visible=False
        threading.Timer(2.0, hide).start()

    def spin_animation(self, final_symbols: list[str]) -> None:
        from time import sleep

        placeholder_label = arcade.gui.UILabel(
            text="?  ?  ?",
            text_color=arcade.color.BLACK,
            font_size=40
        )
        self.box.add(placeholder_label)
        def run_animation():
            for _ in range(15):
                spin_result = [random.choice(["1","2","3","4","5","6"]) for _ in range(3)]
                placeholder_label.text = " ".join(spin_result)
                self.ui.on_draw()
                sleep(0.05)
            placeholder_label.text = " ".join(final_symbols)
        threading.Thread(target=run_animation).start()




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

