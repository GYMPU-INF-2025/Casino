from __future__ import annotations

import typing

import arcade.gui
from arcade import types
from arcade import uicolor
from arcade.gui.widgets import buttons

__all__ = ("BoxLayout", "Button", "ButtonStyle", "Label")


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
