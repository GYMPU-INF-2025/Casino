from __future__ import annotations

import logging
import typing

import arcade
import arcade.gui
import arcade.gui.experimental

import frontend.constants as c
from frontend.net import ClientHTTPError
from frontend.views.base import BaseGUI
import arcade.color as color

if typing.TYPE_CHECKING:
    from frontend.window import MainWindow
    from arcade.types import Color

logger = logging.getLogger(__name__)


class LobbysView(BaseGUI):
    def __init__(self, window: MainWindow, background_color: Color | None = None) -> None:
        super().__init__(window=window)
        self._background_color = background_color

        self._button_width = (c.MENU_WIDTH - c.MENU_SPACING) / 2

        self.grid = arcade.gui.UIGridLayout(
            column_count=2, row_count=4, horizontal_spacing=c.MENU_SPACING, vertical_spacing=c.MENU_SPACING
        )
        self.anchor = self.ui.add(arcade.gui.UIAnchorLayout())

        self.username_field = arcade.gui.UIInputText(width=self._button_width)
        self.password_field = arcade.gui.UIInputText(width=self._button_width)

        self.grid.add(arcade.gui.UILabel(text="Username:", width=self._button_width), column=0, row=0)
        self.grid.add(self.username_field, column=1, row=0)
        self.grid.add(arcade.gui.UILabel(text="Password:", width=self._button_width), column=0, row=1)
        self.grid.add(self.password_field, column=1, row=1)
        login_button = arcade.gui.UIFlatButton(text="Login", width=self._button_width, style=c.BUTTON_STYLE)
        register_button = arcade.gui.UIFlatButton(text="Register", width=self._button_width, style=c.BUTTON_STYLE)
        register_button.set_handler("on_click", self.on_register_click)
        login_button.set_handler("on_click", self.on_login_click)
        self.grid.add(login_button, column=0, row=2)
        self.grid.add(register_button, column=1, row=2)

        self.error_text = arcade.gui.UILabel(text="", text_color=color.RED, width=c.MENU_WIDTH,
                                             align=c.Alignment.CENTER)
        self.grid.add(self.error_text, column=0, column_span=2, row=3)

        self.anchor.add(anchor_y=c.Alignment.CENTER, anchor_x=c.Alignment.CENTER, child=self.grid)

    def reset(self) -> None:
        self.error_text.text = ""
        self.username_field.text = ""
        self.password_field.text = ""

    def on_register_click(self, _: arcade.gui.UIOnClickEvent) -> None:
        logger.info("register")

    def on_login_click(self, _: arcade.gui.UIOnClickEvent) -> None:
        try:
            self.window.net_client.login(username=self.username_field.text, password=self.password_field.text)
        except ClientHTTPError as exc:
            self.error_text.text = exc.detail
        else:
            self.window.show_main_menu()
            self.reset()