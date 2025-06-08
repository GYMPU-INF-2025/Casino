from __future__ import annotations

__all__ = (
    "ASSETS_PATH",
    "CENTER_X",
    "CENTER_Y",
    "DEFAULT_FPS",
    "FULL_SCREEN",
    "MENU_FONT_SIZE",
    "MENU_ITEM_HEIGHT",
    "MENU_SPACING",
    "MENU_WIDTH",
    "SCREEN_HEIGHT",
    "SCREEN_SIZE",
    "SCREEN_WIDTH",
    "UPDATES_PER_SECOND",
    "WINDOW_NAME",
    "Alignment",
)

import enum
from pathlib import Path

import arcade

ASSETS_PATH = Path(__file__).parent.parent / "assets"

SCREEN_SIZE = [800, 500]
SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN_SIZE
WINDOW_NAME, FULL_SCREEN = "Casino", False

UPDATES_PER_SECOND = 144
DEFAULT_FPS = 160

MENU_WIDTH = 700
MENU_SPACING = 16
MENU_ITEM_HEIGHT = 60

MENU_FONT_SIZE = 32


CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2


class Alignment(enum.StrEnum):
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


BACKEND_URL = "http://127.0.0.1"
