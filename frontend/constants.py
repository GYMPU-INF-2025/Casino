from __future__ import annotations

__all__ = ("FULL_SCREEN", "SCREEN_HEIGHT", "SCREEN_WIDTH", "WINDOW_NAME", "Alignment")

import enum

import arcade

SCREEN_SIZE = arcade.get_display_size()
SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN_SIZE
WINDOW_NAME, FULL_SCREEN = "Casino", True

UPDATE_RATE = 1/144
DEFAULT_FPS = 60

MENU_WIDTH = 500
MENU_SPACING = 16


CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2


class Alignment(enum.StrEnum):
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"
