from __future__ import annotations

__all__ = ("MainMenu",)

import typing

from frontend.views.base import BaseView

if typing.TYPE_CHECKING:
    from arcade.types import Color

    from frontend.window import MainWindow


class MainMenu(BaseView):
    def __init__(self, window: MainWindow, background_color: Color | None = None) -> None:
        super().__init__(window=window, background_color=background_color)

    @typing.override
    def on_draw(self) -> bool | None:
        self.clear()
