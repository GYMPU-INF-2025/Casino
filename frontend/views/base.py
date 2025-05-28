from __future__ import annotations

__all__ = ("BaseView",)

import typing

import arcade

if typing.TYPE_CHECKING:
    from arcade.types import Color

    from frontend.window import MainWindow


class BaseView(arcade.View):
    def __init__(self, window: MainWindow, background_color: Color | None = None) -> None:
        self.window = window
        self._background_color = background_color
