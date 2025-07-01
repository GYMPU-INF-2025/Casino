import arcade


class slots_front(Websocket_View):
    def __init__(self, window: MainWindow, game_mode: c.GameModes, lobby_id: str) -> None:
        super().__init__(window, game_mode, lobby_id)
        '''erstellen der Grafischen Oberfläche'''
        self.ui = arcade.gui.UIManager()
        self.anchor = self.ui.add(arcade.gui.UIAnchorLayout(width=1000, height=500))
        self.box = self.anchor.add(arcade.gui.UIBoxLayout(height=500, width=1000))
        button = self.box.add(Button(text="Test", style=ButtonStyle()))
        button.set_handler("on_click", lambda _: self._ws_thread.disconnect())

        ''''''

