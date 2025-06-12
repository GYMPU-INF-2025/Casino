from __future__ import annotations

import logging
import typing

import arcade
import arcade.gui
from arcade.gui import UILabel

from frontend.internal.decorator import add_event_listener
from frontend.internal.websocket_view import WebsocketView
from frontend.ui import Button
from frontend.ui import ButtonStyle
from shared.models import events

if typing.TYPE_CHECKING:
    import frontend.constants as c
    from frontend.window import MainWindow

logger = logging.getLogger(__name__)


class GameView(WebsocketView):
    def __init__(self, window: MainWindow, game_mode: c.GameModes, lobby_id: str) -> None:
        super().__init__(window, game_mode, lobby_id)
        self.ui = arcade.gui.UIManager()
        self.anchor = self.ui.add(arcade.gui.UIAnchorLayout(width=1000, height=500))
        self.box = self.anchor.add(arcade.gui.UIBoxLayout(height=500, width=1000))
        button = self.box.add(Button(text="Test", style=ButtonStyle()))
        button.set_handler("on_click", lambda _: self._ws_thread.disconnect())
        self.money = 0
        self.label = self.box.add(UILabel(text=f"Money: {self.money}", font_size=40))
        button2 = self.box.add(Button(text="Test 2", style=ButtonStyle()))
        button2.set_handler("on_click", self.on_button_press)

    def on_button_press(self, _: arcade.gui.UIOnClickEvent) -> None:
        self.send_event(events.UpdateMoney(money=self.money + 1))

    @add_event_listener(events.ReadyEvent)
    def on_ready(self, ready: events.ReadyEvent) -> None:
        logger.debug("Ready Event Listener triggered! %s", ready.user.username)

    @add_event_listener(events.UpdateMoney)
    def on_money_update(self, event: events.UpdateMoney) -> None:
        self.money = event.money

    @typing.override
    def on_draw(self) -> bool | None:
        super().on_draw()
        self.ui.draw()

    @typing.override
    def on_show_view(self) -> None:
        self.ui.enable()

    @typing.override
    def on_hide_view(self) -> None:
        self.ui.disable()

    @typing.override
    def on_update(self, delta_time: float) -> bool | None:
        super().on_update(delta_time)
        self.label.text = f"Money: {self.money}"
