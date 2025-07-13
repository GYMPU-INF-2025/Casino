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
from shared.models.events import kein_Geld, Spin_Animation, Slots_Win
from functools import partial

if typing.TYPE_CHECKING:
    import frontend.constants as c
    from frontend.window import MainWindow

class SlotsView(WebsocketView):
    def __init__(self, window: MainWindow, game_mode: c.GameModes, lobby_id: str) -> None:
        super().__init__(window, game_mode, lobby_id)
        '''Erstellen der grafischen Oberfläche'''
        self.ui = arcade.gui.UIManager()

        self.anchor = self.ui.add(arcade.gui.UIAnchorLayout(width=1000, height=500))

        main_layout = arcade.gui.UIBoxLayout(vertical=True, align="center", space_between=20)
        self.anchor.add(main_layout)

        self.symbol_row = arcade.gui.UIBoxLayout(vertical=False, align="center", space_between=20)
        main_layout.add(self.symbol_row)

        self.box = arcade.gui.UIBoxLayout(height=100, width=1000)
        main_layout.add(self.box)

        # Lade Symbole
        self.symbol_textures = {
            "a": arcade.load_texture("assets/slots_symbols/cherry.png"),
            "b": arcade.load_texture("assets/slots_symbols/diamond.png"),
            "c": arcade.load_texture("assets/slots_symbols/bell.png"),
            "d": arcade.load_texture("assets/slots_symbols/heart.png"),
            "e": arcade.load_texture("assets/slots_symbols/apple.png"),
            "f": arcade.load_texture("assets/slots_symbols/horseiron.png"),
        }

        self.animation_running = False
        self.animation_step = 0
        self.max_animation_steps = 10
        money = self.send_event(events.Moneyq)

        self.money_label = arcade.gui.UILabel(
            text= self.send_event(events.Moneyq),
            text_color=arcade.color.GREEN,
            font_size=40
        )
        self.send_event(events.moneyq)
        self.box.add(self.money_label)

        # Symbole mit Rahmen simulieren (kein border support, daher Rahmen selbst zeichnen)
        self.slot_images = []
        self.slot_positions = []  # für Rahmen-Zeichnung speichern
        for i in range(3):
            btn = arcade.gui.UITextureButton(
                texture=self.symbol_textures["a"],
                width=90,
                height=90,
                style={
                    "normal" : arcade.gui.UITextureButton.UIStyle(

                    )

                })
            btn.background_color = arcade.color.WHITE

            self.slot_images.append(btn)
            self.symbol_row.add(btn)

        button = Button(text="Spin", style=ButtonStyle())
        main_layout.add(button)
        button.set_handler("on_click", self.on_button_press)

        self.message_label = arcade.gui.UILabel(
            text="",
            text_color=arcade.color.RED,
            font_size=20,
            width=400,
            height=40,
        )
        main_layout.add(self.message_label)

    def on_button_press(self, _: arcade.gui.UIOnClickEvent) -> None:
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
        SlotSymbols = list(self.symbol_textures.keys())  # a–f

        # Zufällige Bilder während der Animation
        for i in range(3):
            symbol = random.choice(SlotSymbols)
            texture = self.symbol_textures[symbol]
            self.slot_images[i].texture = texture

        # Wenn Animation fertig → finale Symbole setzen
        if self.animation_step >= self.max_animation_steps:
            self.animation_running = False
            self.animation_step = 0
            arcade.unschedule(self.update_animation_wrapper)

            for i in range(3):
                final_symbol = final_symbols[i]
                texture = self.symbol_textures.get(final_symbol)
                self.slot_images[i].texture = texture

    def update_animation_wrapper(self, final_symbols: list[str], delta_time: float) -> None:
        self.update_animation(final_symbols, delta_time)

    @add_event_listener(Slots_Win)
    def Money_now(self, now_money: int) -> None:
        self.money_label.text = f"Geld: {now_money}"

    @add_event_listener(Spin_Animation)
    def Spin_Animation(self, event: events.Spin_Animation) -> None:
        self.animation_running = True
        self.animation_step = 0
        animation_func = partial(self.update_animation_wrapper, event.final_symbols)
        arcade.schedule(animation_func, 0.1)

    @typing.override
    def on_draw(self) -> bool | None:
        super().on_draw()
        self.ui.draw()

        # Rahmen zeichnen (rechteckiger Rahmen um jedes Symbol)
        for btn in self.slot_images:
            x, y = btn.center_x, btn.center_y
            width, height = btn.width, btn.height
            arcade.draw_lbwh_rectangle_outline(x, y, width, height, arcade.color.GRAY, border_width=3)

    @typing.override
    def on_show_view(self) -> None:
        self.ui.enable()

    @typing.override
    def on_hide_view(self) -> None:
        self.ui.disable()
