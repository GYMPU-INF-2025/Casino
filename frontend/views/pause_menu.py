from __future__ import annotations

__all__ = ("PauseMenu",)

import logging
import typing

import arcade
import arcade.gui
from arcade.experimental import Shadertoy
from arcade.types import Color

import frontend.constants as c
from frontend.views.base import BaseGUI

if typing.TYPE_CHECKING:
    from frontend.window import MainWindow


logger = logging.getLogger(__name__)


class PauseMenu(BaseGUI):
    """View used for the pause menu. This menu opens when you press `ESC`.

    The only "special" thing about this view is that it draws the view
    that was active before this one as the background and blurs it.
    This is achieved by using a shader.

    Authors: Christopher
    """

    def __init__(self, window: MainWindow) -> None:
        super().__init__(window=window)

        self._shown = False

        self._button_width = (c.MENU_WIDTH - c.MENU_SPACING) / 2

        self.grid = arcade.gui.UIGridLayout(
            column_count=2, row_count=3, horizontal_spacing=c.MENU_SPACING, vertical_spacing=c.MENU_SPACING
        )
        self.anchor = self.ui.add(arcade.gui.UIAnchorLayout())

        main_menu_button = arcade.gui.UIFlatButton(text="Main Menu", width=c.MENU_WIDTH)
        close_menu_button = arcade.gui.UIFlatButton(text="Close Menu", width=c.MENU_WIDTH)
        close_game_button = arcade.gui.UIFlatButton(text="Quit Game", width=c.MENU_WIDTH)

        @main_menu_button.event("on_click")
        def on_main_menu_button(_: arcade.gui.UIOnClickEvent) -> None:
            self.window.show_main_menu()

        @close_menu_button.event("on_click")
        def on_close_menu_button(_: arcade.gui.UIOnClickEvent) -> None:
            self.window.toggle_pause_menu()

        @close_game_button.event("on_click")
        def on_close_game_button(_: arcade.gui.UIOnClickEvent) -> None:
            arcade.exit()

        self.grid.add(child=main_menu_button, column=0, row=0, column_span=2)
        self.grid.add(child=close_menu_button, column=0, row=1, column_span=2)
        self.grid.add(child=close_game_button, column=0, row=2, column_span=2)

        self.anchor.add(anchor_y=c.Alignment.CENTER, anchor_x=c.Alignment.CENTER, child=self.grid)

        self.fbo = self.window.ctx.framebuffer(color_attachments=[self.window.ctx.texture(c.SCREEN_SIZE)])
        self.blur_shader = Shadertoy.create_from_file(c.SCREEN_SIZE, self.window.get_shader_path("blur"))
        self.blur_shader.program["uRadius"] = 2.0

    @typing.override
    def on_draw(self) -> None:
        self.clear()
        self.fbo.use()
        self.window.current_selected_view.on_draw()
        self.window.ctx.screen.use()
        self.blur_shader.channel_0 = self.fbo.color_attachments[0]
        self.blur_shader.render()
        arcade.draw_rect_filled(self.window.rect, color=Color(0, 0, 0, 120))
        self.ui.draw()
