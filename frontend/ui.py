from __future__ import annotations

import collections.abc
import logging
import typing

import arcade.gui
from arcade import types
from arcade import uicolor
from arcade.gui.widgets import buttons
from arcade.gui.widgets import text

__all__ = ("BoxLayout", "Button", "ButtonStyle", "InputText", "Label")


logger = logging.getLogger(__name__)


class ButtonStyle:
    def __init__(self, font_size: int = 20) -> None:
        self.normal = buttons.UIFlatButtonStyle(
            font_color=uicolor.WHITE_CLOUDS, bg=types.Color(0, 0, 0, 150), font_size=font_size
        )
        self.hover = buttons.UIFlatButtonStyle(
            bg=types.Color(0, 0, 0, 190), font_color=uicolor.WHITE_CLOUDS, font_size=font_size
        )
        self.press = buttons.UIFlatButtonStyle(bg=uicolor.WHITE_SILVER, font_color=uicolor.BLACK, font_size=font_size)
        self.disabled = buttons.UIFlatButtonStyle(
            font_color=uicolor.WHITE_CLOUDS, bg=types.Color(0, 0, 0, 90), font_size=font_size
        )

    def dict(self) -> dict[str, buttons.UIFlatButtonStyle]:
        return {"normal": self.normal, "hover": self.hover, "press": self.press, "disabled": self.disabled}


class BoxLayout(arcade.gui.UIBoxLayout):
    @typing.override
    def _update_size_hints(self) -> None:
        return


class Label(arcade.gui.UILabel):
    _min_size_x = -1

    @typing.override
    def _update_size_hint_min(self) -> None:
        super()._update_size_hint_min()
        if self._min_size_x > 0 and self.size_hint_min[0] < self._min_size_x:
            self.size_hint_min = (self._min_size_x, self.size_hint_min[1])

    def set_min_size_x(self, min_size_x: int) -> Label:
        self._min_size_x = min_size_x
        self._update_size_hint_min()
        self.fit_content()
        return self


class Button(arcade.gui.UIFlatButton):
    def __init__(
        self,
        *,
        x: float = 0,
        y: float = 0,
        width: float = 100,
        height: float = 50,
        text: str = "",
        multiline: bool = False,
        size_hint: tuple[float | None, float | None] | None = None,
        size_hint_min: tuple[float | None, float | None] | None = None,
        size_hint_max: tuple[float | None, float | None] | None = None,
        style: ButtonStyle | None = None,
    ) -> None:
        if not style:
            style = ButtonStyle()
        super().__init__(
            x=x,
            y=y,
            width=width,
            height=height,
            text=text,
            multiline=multiline,
            size_hint=size_hint,
            size_hint_min=size_hint_min,
            size_hint_max=size_hint_max,
            style=style.dict(),
        )


class InputText(arcade.gui.UIInputText):
    """Custom Text Input class.

    This is needed because there exists a bug in arcade that TextInputs do not
    deactivate automatically. Only thing changed compared to the normal `arcade.gui.UIInputText`
    is that you need to pass a `arcade.gui.UIManager` to the constructor.

    Linked Issues:
    https://github.com/pythonarcade/arcade/issues/2725
    https://github.com/GYMPU-INF-2025/Casino/issues/13

    Authors: Christopher
    """

    @typing.override
    def __init__(
        self,
        ui_manager: arcade.gui.UIManager,
        *,
        x: float = 0,
        y: float = 0,
        width: float = 100,
        height: float = 25,
        text: str = "",
        font_name: collections.abc.Sequence[str] = ("Arial",),
        font_size: float = 12,
        text_color: arcade.types.RGBOrA255 = arcade.color.WHITE,
        multiline: bool = False,
        caret_color: arcade.types.RGBOrA255 = arcade.color.WHITE,
        border_color: arcade.types.Color | None = arcade.color.WHITE,
        border_width: int = 2,
        size_hint: tuple[float | None, float | None] | None = None,
        size_hint_min: tuple[float | None, float | None] | None = None,
        size_hint_max: tuple[float | None, float | None] | None = None,
        style: dict[str, text.UIInputTextStyle] | None = None,
        **kwargs: typing.Any,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            width=width,
            height=height,
            text=text,
            font_name=font_name,
            font_size=font_size,
            text_color=text_color,
            multiline=multiline,
            caret_color=caret_color,
            border_color=border_color,
            border_width=border_width,
            size_hint=size_hint,
            size_hint_min=size_hint_min,
            size_hint_max=size_hint_max,
            style=style,
            kwargs=kwargs,
        )
        self.ui_manager = ui_manager

    @typing.override
    def activate(self) -> None:
        def recursive_deactivate(children: collections.abc.Sequence[arcade.gui.UIWidget] | arcade.gui.UIWidget) -> None:
            if isinstance(children, collections.abc.Sequence):
                for c in children:
                    recursive_deactivate(c)
            elif isinstance(children, InputText):
                children.deactivate()
            elif hasattr(children, "children"):
                recursive_deactivate(children.children)

        for child in self.ui_manager.children.values():
            recursive_deactivate(child)
        super().activate()
