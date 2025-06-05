from __future__ import annotations

__all__ = (
    "CENTER_X",
    "CENTER_Y",
    "DEFAULT_FPS",
    "FULL_SCREEN",
    "MENU_SPACING",
    "MENU_WIDTH",
    "SCREEN_HEIGHT",
    "SCREEN_SIZE",
    "SCREEN_WIDTH",
    "UPDATES_PER_SECOND",
    "WINDOW_NAME",
    "BUTTON_STYLE",
    "Alignment",
)

import enum

import arcade
from arcade import uicolor
from arcade.gui.widgets.buttons import UIFlatButtonStyle

SCREEN_SIZE = arcade.get_display_size()
SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN_SIZE
WINDOW_NAME, FULL_SCREEN = "Casino", True

UPDATES_PER_SECOND = 144
DEFAULT_FPS = 160

MENU_WIDTH = 500
MENU_SPACING = 16


CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2


BUTTON_STYLE = {
        "normal": UIFlatButtonStyle(
            font_color=uicolor.WHITE_CLOUDS,
            bg=uicolor.BLACK,
            border=uicolor.WHITE_CLOUDS,
            border_width=2,
        ),
        "hover": UIFlatButtonStyle(
            bg=uicolor.WHITE_CLOUDS,
            font_color=uicolor.BLACK,
        ),
        "press": UIFlatButtonStyle(
            bg=uicolor.WHITE_SILVER,
            font_color=uicolor.BLACK,
        ),
        "disabled": UIFlatButtonStyle(
            bg=uicolor.GRAY_ASBESTOS,
        ),
    }

class Alignment(enum.StrEnum):
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"


BACKEND_URL = "http://127.0.0.1"
