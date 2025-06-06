from __future__ import annotations

__all__ = ("TitleView",)

import time
import typing

import arcade
import arcade.color as color
from arcade.types import Color

import frontend.constants as c
from frontend.views.base import BaseGameView

if typing.TYPE_CHECKING:
    from frontend.window import MainWindow


class TitleView(BaseGameView):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window=window)

        self.text_lines = [
            "This game is an online casino simulation.",
            "",
            "Gambling is dangerous please don't gamble with real money.",
            "If you want to spend money feel free to donate me some money.",
            "",
            "Press any key to continue",
            "",
            "",
            "Copyright © 2025 gympu",
        ]
        self.timer: float = time.time()

        self.alpha = 0
        self.text: arcade.Text = arcade.Text(
            text="\n".join(self.text_lines),
            x=c.CENTER_X,
            y=c.CENTER_Y,
            font_size=24,
            color=self.get_color(),
            align=c.Alignment.CENTER,
            anchor_x=c.Alignment.CENTER,
            anchor_y=c.Alignment.CENTER,
            width=c.SCREEN_WIDTH,
            multiline=True,
        )

    def get_color(self) -> Color:
        return Color(255, 255, 255, self.alpha)

    def on_input(self) -> None:
        self.window.show_main_menu()

    @typing.override
    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        self.on_input()

    @typing.override
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        self.on_input()

    @typing.override
    def on_draw(self) -> bool | None:
        self.clear()
        arcade.draw_rect_filled(rect=self.window.rect, color=color.BLACK)
        elapsed = time.time() - self.timer

        t = elapsed / 3.3
        if t <= 1:
            self.alpha = int(255 * t)

        self.text.color = self.get_color()
        self.text.draw()
        
        

    @typing.override
    def on_show_view(self) -> None:
        self.timer = time.time()
