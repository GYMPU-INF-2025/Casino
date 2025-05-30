from __future__ import annotations

__all__ = ("BaseGUI", "BaseGameView", "BaseView")

import abc
import typing

import arcade
import arcade.gui

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
    def __init__(self, window: MainWindow, background_color: Color | None = None) -> None:
        self.window = window
        self._background_color = background_color

    @property
    @typing.override
    def can_pause(self) -> bool:
        return True


class BaseGUI(arcade.gui.UIView, BaseView):
    @typing.override
    def __init__(self, window: MainWindow) -> None:
        self.window = window
        super().__init__()

    @property
    @typing.override
    def can_pause(self) -> bool:
        return False
