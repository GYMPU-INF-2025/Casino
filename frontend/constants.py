from __future__ import annotations

__all__ = ("FULL_SCREEN", "SCREEN_HEIGHT", "SCREEN_WIDTH", "WINDOW_NAME", "Alignment")

import enum

import arcade

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()
WINDOW_NAME, FULL_SCREEN = "Casino", True


CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2


class Alignment(enum.StrEnum):
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"
