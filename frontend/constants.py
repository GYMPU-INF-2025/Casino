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
    "ASSETS_PATH",
    "BUTTON_BLACK",
    "MENU_ITEM_HEIGHT",
    "MENU_FONT_SIZE",
    "Alignment",
)

import enum
from pathlib import Path

import arcade
from arcade import uicolor
from arcade.gui.widgets.buttons import UIFlatButtonStyle
from arcade.types import Color

ASSETS_PATH = Path(__file__).parent.parent / "assets"

SCREEN_SIZE = arcade.get_display_size()
SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN_SIZE
WINDOW_NAME, FULL_SCREEN = "Casino", True

UPDATES_PER_SECOND = 144
DEFAULT_FPS = 160

MENU_WIDTH = 700
MENU_SPACING = 16
MENU_ITEM_HEIGHT = 60

MENU_FONT_SIZE = 32


CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2

BUTTON_BLACK = Color(0, 0, 0, 150)

BUTTON_STYLE = {
        "normal": UIFlatButtonStyle(
            font_color=uicolor.WHITE_CLOUDS,
            bg=BUTTON_BLACK,
            font_size=20,
        ),
        "hover": UIFlatButtonStyle(
            bg=uicolor.WHITE_CLOUDS,
            font_color=uicolor.BLACK,
            font_size=20,
        ),
        "press": UIFlatButtonStyle(
            bg=uicolor.WHITE_SILVER,
            font_color=uicolor.BLACK,
            font_size=20,
        ),
        "disabled": UIFlatButtonStyle(
            bg=uicolor.GRAY_ASBESTOS,
        ),
    }

class Alignment(enum.StrEnum):
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


BACKEND_URL = "http://127.0.0.1"
