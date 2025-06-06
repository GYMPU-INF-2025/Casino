from __future__ import annotations

import arcade.gui
from arcade import uicolor
from arcade.gui.widgets import buttons

__all__ = ("Button", "ButtonStyle")


class ButtonStyle:
    def __init__(self, font_size: int = 20) -> None:
        self.normal = buttons.UIFlatButtonStyle(
            font_color=uicolor.WHITE_CLOUDS, bg=uicolor.Color(0, 0, 0, 150), font_size=font_size
        )
        self.hover = buttons.UIFlatButtonStyle(
            bg=uicolor.Color(0, 0, 0, 190), font_color=uicolor.WHITE_CLOUDS, font_size=font_size
        )
        self.press = buttons.UIFlatButtonStyle(bg=uicolor.WHITE_SILVER, font_color=uicolor.BLACK, font_size=font_size)
        self.disabled = buttons.UIFlatButtonStyle(bg=uicolor.GRAY_ASBESTOS)

    def dict(self) -> dict[str, buttons.UIFlatButtonStyle]:
        return {"normal": self.normal, "hover": self.hover, "press": self.press, "disabled": self.disabled}


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
