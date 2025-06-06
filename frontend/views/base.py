from __future__ import annotations

__all__ = ("BaseGUI", "BaseGameView", "BaseView")

import abc
import typing

import arcade
import arcade.gui
import frontend.constants as c

if typing.TYPE_CHECKING:
    from arcade.types import Color

    from frontend.window import MainWindow


class BaseView(abc.ABC, arcade.View):
    @property
    @abc.abstractmethod
    def can_pause(self) -> bool:
        pass

        
        

class BaseGameView(BaseView):
    @typing.override
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window, background_color=None)
        self.window = window
        self._background_image = arcade.load_texture(c.ASSETS_PATH / "background.png")

    @property
    @typing.override
    def can_pause(self) -> bool:
        return True

    @typing.override
    def on_draw(self) -> bool | None:
        self.clear()
        arcade.draw_texture_rect(
            self._background_image,
            self.window.rect
        )


class BaseGUI(arcade.gui.UIView, BaseView):
    @typing.override
    def __init__(self, window: MainWindow) -> None:
        self.window = window
        super().__init__()
        self._background_image = arcade.load_texture(c.ASSETS_PATH / "background.png")

    @property
    @typing.override
    def can_pause(self) -> bool:
        return False

    @typing.override
    def on_draw(self) -> None:
        self.clear()
        arcade.draw_texture_rect(
            self._background_image,
            self.window.rect
        )
        self.on_draw_before_ui()
        self.ui.draw()
        self.on_draw_after_ui()
