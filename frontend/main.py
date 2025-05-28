from __future__ import annotations

import json
import logging.config
import pathlib

import arcade
import arcade.gui

from frontend.window import MainWindow

ROOT_PATH = pathlib.Path(__file__).parent

"""
class IdentifyData(msgspec.Struct):
    token: str = msgspec.field()

class Identify(msgspec.Struct):
    d: IdentifyData
    op: int = msgspec.field(default=2)

class UpdateMoneyData(msgspec.Struct):
    money: int

class UpdateMoney(msgspec.Struct):
    d: UpdateMoneyData
    t: str = msgspec.field(default="UPDATE_MONEY")
    op: int = msgspec.field(default=0)


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Counter with WebSocket (sync)"
WS_SERVER_URL = "ws://127.0.0.1:8000/test/test123"  # WebSocket Server URL


class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.background_color = arcade.color.AMAZON
        self.counter = 0
        self.ws: websocket.WebSocket | None = None

        # UI setup
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.layout = arcade.gui.UIAnchorLayout()

        self.label = arcade.gui.UILabel(text=str(self.counter), font_size=40)
        self.layout.add(self.label, anchor_x="center", anchor_y="center")

        plus_button = arcade.gui.UIFlatButton(text="+", width=60)
        minus_button = arcade.gui.UIFlatButton(text="-", width=60)
        plus_button.on_click = self.increase
        minus_button.on_click = self.decrease

        hbox = arcade.gui.UIBoxLayout(vertical=False, space_between=20)
        hbox.add(minus_button)
        hbox.add(plus_button)
        self._pending_money = None
        self.layout.add(hbox, anchor_x="center", anchor_y="bottom", align_y=50)
        self.manager.add(self.layout)

        # Start the WebSocket client in a separate thread
        threading.Thread(target=self.ws_loop, daemon=True).start()

    def increase(self, event):
        self.counter += 1
        self.label.text = str(self.counter)
        self.send_counter()

    def decrease(self, event):
        self.counter -= 1
        self.label.text = str(self.counter)
        self.send_counter()

    def send_counter(self):
        if self.ws:
            try:
                msg = msgspec.json.encode(UpdateMoney(d=UpdateMoneyData(money=self.counter)))
                self.ws.send(msg)
            except Exception as e:
                print(f"[WebSocket Send Error] {e}")

    def ws_loop(self):
        try:
            self.ws = websocket.create_connection(WS_SERVER_URL)
            print("[WebSocket] Connected")

            hello_msg = self.ws.recv()
            print(f"[WebSocket] Hello: {hello_msg}")

            self.ws.send(msgspec.json.encode(Identify(d=IdentifyData(token=os.environ["TOKEN"]))))
            ready_msg = self.ws.recv()
            print(f"[WebSocket] Ready: {ready_msg}")

            while True:
                msg = self.ws.recv()
                print(f"[WebSocket] Message: {msg}")
                try:
                    update_money = msgspec.json.decode(msg, type=UpdateMoney)
                except Exception as e:
                    print(f"[MSGSPEC Error] {e}")
                else:
                    try:
                        self._pending_money = update_money.d.money
                        self.label.text = str(self.counter)
                    except Exception as e:
                        print(f"[Some Error] {e}")

        except Exception as e:
            print(f"[WebSocket Error] {e}")
            self.ws = None

    def on_draw(self):
        self.clear()
        self.manager.draw()

    def on_update(self, delta_time: float):
        if self._pending_money is not None and self.counter != self._pending_money:
            self.counter = self._pending_money
            self.label.text = str(self.counter)
"""


def main() -> None:
    MainWindow()
    arcade.run()


if __name__ == "__main__":
    with (ROOT_PATH / "logging.json").open() as f:
        logging.config.dictConfig(json.load(f))
    main()
