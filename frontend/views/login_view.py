from __future__ import annotations

import logging
import typing

import arcade
import arcade.gui
import arcade.gui.experimental
from arcade import color

import frontend.constants as c
from frontend import ui
from frontend.net import HTTPResponseError
from frontend.views.base import BaseGUI

if typing.TYPE_CHECKING:
    from frontend.window import MainWindow
logger = logging.getLogger(__name__)


class LoginMenu(BaseGUI):
    """Login view used to log in / register.

    Authors: Christopher, Quirin
    """
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window=window)

        self._button_width = (c.MENU_WIDTH - c.MENU_SPACING) / 2

        self.grid = arcade.gui.UIGridLayout(
            column_count=2, row_count=4, horizontal_spacing=c.MENU_SPACING, vertical_spacing=c.MENU_SPACING
        )
        self.anchor = self.ui.add(arcade.gui.UIAnchorLayout())

        self.username_field = ui.InputText(
            ui_manager=self.ui, width=self._button_width, height=c.MENU_ITEM_HEIGHT, font_size=c.MENU_FONT_SIZE
        )
        self.password_field = ui.InputText(
            ui_manager=self.ui, width=self._button_width, height=c.MENU_ITEM_HEIGHT, font_size=c.MENU_FONT_SIZE
        )

        self.grid.add(
            arcade.gui.UILabel(text="Username:", width=self._button_width, font_size=c.MENU_FONT_SIZE), column=0, row=0
        )
        self.grid.add(self.username_field, column=1, row=0)
        self.grid.add(
            arcade.gui.UILabel(text="Password:", width=self._button_width, font_size=c.MENU_FONT_SIZE), column=0, row=1
        )
        self.grid.add(self.password_field, column=1, row=1)
        login_button = ui.Button(text="Login", width=self._button_width, height=c.MENU_ITEM_HEIGHT)
        register_button = ui.Button(text="Register", width=self._button_width, height=c.MENU_ITEM_HEIGHT)
        register_button.set_handler("on_click", self.on_register_click)
        login_button.set_handler("on_click", self.on_login_click)
        self.grid.add(login_button, column=0, row=2)
        self.grid.add(register_button, column=1, row=2)

        self.error_text = arcade.gui.UILabel(
            text="", text_color=color.RED, width=c.MENU_WIDTH, align=c.Alignment.CENTER, font_size=c.MENU_FONT_SIZE - 10
        )
        self.grid.add(self.error_text, column=0, column_span=2, row=3)

        self.anchor.add(anchor_y=c.Alignment.CENTER, anchor_x=c.Alignment.CENTER, child=self.grid)

    def reset(self) -> None:
        """Function that resets all the texts."""
        self.error_text.text = ""
        self.username_field.text = ""
        self.password_field.text = ""

    def on_register_click(self, _: arcade.gui.UIOnClickEvent) -> None:
        """Callback when the register button got pressed.

        It first checks if username/password is empty and if not it creates a user and then logs in with
        the credentials. If any request fails, it shows an error text. Otherwise, it continues to the main menu.
        """
        if not self.textfield_check():
            return

        try:
            self.window.net_client.rest.register(username=self.username_field.text, password=self.password_field.text)
        except HTTPResponseError as exc:
            self.error_text.text = exc.detail
            return

        try:
            self.window.net_client.login(username=self.username_field.text, password=self.password_field.text)
        except HTTPResponseError as exc:
            self.error_text.text = exc.detail
        else:
            self.window.show_main_menu()
            self.reset()

    def on_login_click(self, _: arcade.gui.UIOnClickEvent) -> None:
        """Callback when the login button got pressed.

        It first checks if username/password is empty and if not it trys to log in with the given credentials.
        If the requests fails it displays an error text. Otherwise, it continues to the main menu.
        """
        if not self.textfield_check():
            return

        try:
            self.window.net_client.login(username=self.username_field.text, password=self.password_field.text)
        except HTTPResponseError as exc:
            self.error_text.text = exc.detail
        else:
            self.window.show_main_menu()
            self.reset()

    def textfield_check(self) -> bool:
        """Helper function to check if any of the text inputs are emtpy."""
        if not self.username_field.text or not self.password_field.text:
            self.error_text.text = "Username and password cannot be empty."
            return False
        return True
