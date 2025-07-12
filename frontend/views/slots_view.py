from __future__ import annotations

import logging
import random
import threading
import typing

import arcade
import arcade.gui
from arcade.gui import UILabel
from pymunk.examples.spiderweb import on_draw

import backend.main
from frontend.internal.decorator import add_event_listener
from frontend.internal.websocket_view import WebsocketView
from frontend.ui import Button
from frontend.ui import ButtonStyle
from shared.models import events
from shared.models.events import kein_Geld, Spin_Animation

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

        '''button = self.box.add(Button(text="Test", style=ButtonStyle()))
        button.set_handler("on_click", self.on_button_press)
        '''
        button = self.box.add(Button(text="turn", style=ButtonStyle()))
        button.set_handler( "on_click",self.on_button_press)



        self.message_label = arcade.gui.UILabel(
            text="",
            text_color=arcade.color.RED,
            font_size=20,
            width=400,
            height=40,

        )
        self.UILabel = ""
        self.box.add(self.message_label)
        self.message_label.center_on_screen()

        ''''''
        from time import sleep



        placeholder_label = arcade.gui.UILabel(
            text="?  ?  ?",
            text_color=arcade.color.BLACK,
            font_size=40
        )
        self.box.add(placeholder_label)





    def on_button_press(self, _: arcade.gui.UIOnClickEvent) -> None:
        self.send_event(events.StartSpin(einsatz=20))

    '''def button2_on_press(self, _: arcade.gui.UIOnClickEvent) -> None:
        self.send_event(events.StartSpin(einsatz=20))'''

    @add_event_listener(kein_Geld)
    def kein_Geld(self, _: arcade.gui.UIOnClickEvent) -> None:
        self.message_label.text ="Nicht genug Geld!"
        print("kein_Geld")
        self.window.dispatch_event("on_draw")
        self.message_label.visible=True
        self.window.dispatch_event("on_draw")

        def hide():
            self.message_label.visible=False
        threading.Timer(20, hide).start()
        self.window.dispatch_event("on_draw")


    @add_event_listener(Spin_Animation)
    def Spin_Animation(self, final_symbols: list) -> None:
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
                placeholder_label.text = "".join(spin_result)
                self.window.dispatch_event("on_draw")
                sleep(0.05)
            placeholder_label.text = " ".join(final_symbols)

            self.window.dispatch_event("on_draw")
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

