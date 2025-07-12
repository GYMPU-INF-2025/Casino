from __future__ import annotations

import random
import typing

import arcade
import arcade.gui
from frontend.internal.decorator import add_event_listener
from frontend.internal.websocket_view import WebsocketView
from frontend.ui import Button
from frontend.ui import ButtonStyle
from shared.models import events
from shared.models.events import kein_Geld, Spin_Animation
from functools import partial

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
        
        self.animation_running = False
        self.animation_step = 0
        self.max_animation_steps = 10

        self.placeholder_label = arcade.gui.UILabel(
            text="?  ?  ?",
            text_color=arcade.color.BLACK,
            font_size=40
        )
        self.box.add(self.placeholder_label)

        button = self.box.add(Button(text="Test", style=ButtonStyle()))
        button.set_handler("on_click", self.on_button_press)
        button = self.box.add(Button(text="turn", style=ButtonStyle()))
        button.set_handler("on_click", self.on_button_press)

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

    def on_button_press(self, _: arcade.gui.UIOnClickEvent) -> None:
        self.send_event(events.StartSpin(einsatz=20))

    def button2_on_press(self, _: arcade.gui.UIOnClickEvent) -> None:
        self.send_event(events.StartSpin(einsatz=20))

    @add_event_listener(kein_Geld)
    def kein_Geld(self, _: arcade.gui.UIOnClickEvent) -> None:
        self.message_label.text = "Nicht genug Geld!"
        self.message_label.visible = True
        arcade.schedule(lambda dt: setattr(self.message_label, 'visible', False), 2.0)

    def update_animation(self, final_symbols: list[str], delta_time: float) -> None:
        if not self.animation_running:
            return

        self.animation_step += 1
        SlotSymbols = ["a", "b", "c", "d", "e", "f"]
        numbers = [random.choice(SlotSymbols) for _ in range(3)]
        self.placeholder_label.text = " ".join(numbers)

        if self.animation_step >= self.max_animation_steps:
            self.animation_running = False
            self.animation_step = 0
            arcade.unschedule(self.update_animation_wrapper)
            self.placeholder_label.text = " " + " ".join(final_symbols)

    def update_animation_wrapper(self, final_symbols: list[str], delta_time: float) -> None:
        self.update_animation(final_symbols, delta_time)

    @add_event_listener(Spin_Animation)
    def Spin_Animation(self, event: events.Spin_Animation) -> None:
        self.animation_running = True
        self.animation_step = 0
        # Verwenden von partial um die final_symbols zu übergeben
        animation_func = partial(self.update_animation_wrapper, event.final_symbols)
        arcade.schedule(animation_func, 0.1)

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