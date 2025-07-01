from __future__ import annotations


import typing

import arcade.gui
from frontend.internal.decorator import add_event_listener

from frontend.internal.websocket_view import WebsocketView
from frontend.ui import Button, ButtonStyle
from shared.models import events

if typing.TYPE_CHECKING:
    from frontend import constants as c
    from frontend.window import MainWindow

class BlackjackView(WebsocketView):

    def __init__(self, window: MainWindow, game_mode: c.GameModes, lobby_id: str) -> None:
        super().__init__(window, game_mode, lobby_id)
        self.ui = arcade.gui.UIManager()
        button = self.ui.add(Button(text="Test", style=ButtonStyle()))
        button.set_handler("on_click",self.on_button)

    def on_button(self, _: arcade.gui.UIOnClickEvent) -> None:
        self.send_event(events.PrintText(text="Test"))

    @add_event_listener(events.PrintText)
    def on_print(self, event: events.PrintText) -> None:
        print(event.text)

    def on_draw(self) -> bool | None:
        super().on_draw()
        self.ui.draw()


    @typing.override
    def on_show_view(self) -> None:
        self.ui.enable()

    @typing.override
    def on_hide_view(self) -> None:
        self.ui.disable()


    
