from __future__ import annotations

import logging
import typing

import arcade
import arcade.gui
from arcade.gui import UIAnchorLayout
from arcade.gui.widgets.buttons import UITextureButton

from backend.internal.ws import add_event_listener
from frontend.constants import SCREEN_HEIGHT, SCREEN_WIDTH, Alignment, GameModes
from frontend.internal.websocket_view import WebsocketView
from shared.models import events

if typing.TYPE_CHECKING:
    from frontend.window import MainWindow

logger = logging.getLogger(__name__)

# Constants
STAKE_STEP = 100
MAX_STEPS = 10
ALIVE_IMG_PATH = 'assets/chickengame/alive_img.png'
BUTTON_IMG_PATH = 'assets/chickengame/button.png'
STREET_IMG_PATH = 'assets/chickengame/street.png'
STEP_IMG_PATH = 'assets/chickengame/img.png'


class ChickengameView(WebsocketView):
    def __init__(self, window: MainWindow, game_mode: GameModes, lobby_id: str) -> None:
        super().__init__(window=window, game_mode=game_mode, lobby_id=lobby_id)
        self.ui = arcade.gui.UIManager()

        # UI constants
        self._button_width = SCREEN_WIDTH / 6
        self._button_height = SCREEN_HEIGHT / 6
        self._steps_width = SCREEN_WIDTH / 10
        self._steps_height = (SCREEN_HEIGHT / 3) * 2

        # Game state
        self.gamemode = 0
        self.gamemode_list = ['Easy', 'Medium', 'Hard']
        self.stake = 0
        self.take = 0
        self.total = 0
        self.step = 1
        self.multiplier = 0
        self.step_text = 0

        # Textures
        self.img = arcade.load_texture(STEP_IMG_PATH)
        self.button_img = arcade.load_texture(BUTTON_IMG_PATH)
        self.street_img = arcade.load_texture(STREET_IMG_PATH)

        # UI setup
        self._create_grids()
        self._show_money()
        self._show_steps()
        self._show_buttons()

        for i in range(1, len(self.steps)):
            self.steps[i].disabled = True

    def _create_grids(self) -> None:
        def make_grid(columns, rows, height):
            return arcade.gui.UIGridLayout(
                column_count=columns, row_count=rows,
                row_height=height, size_hint=(None, None),
                width=SCREEN_WIDTH, height=height
            )

        self.grid_top = make_grid(3, 1, self._button_height)
        self.grid_mid = make_grid(MAX_STEPS, 1, self._steps_height)
        self.grid_bottom = make_grid(7, 1, self._button_height)

        self.anchor_top = self.ui.add(UIAnchorLayout())
        self.anchor_mid = self.ui.add(UIAnchorLayout())
        self.anchor_bottom = self.ui.add(UIAnchorLayout())

        self.anchor_top.add(anchor_y=Alignment.TOP, anchor_x=Alignment.CENTER, child=self.grid_top)
        self.anchor_mid.add(anchor_y=Alignment.CENTER, anchor_x=Alignment.CENTER, child=self.grid_mid)
        self.anchor_bottom.add(anchor_y=Alignment.BOTTOM, anchor_x=Alignment.CENTER, child=self.grid_bottom)

    def _show_money(self) -> None:
        def make_label(text: str) -> arcade.gui.UILabel:
            return arcade.gui.UILabel(
                text=text,
                width=SCREEN_WIDTH / 3,
                height=self._button_height,
                font_size=50,
                align=Alignment.CENTER,
            )

        self.stake_label = make_label(f'Stake: {int(self.stake)}')
        self.gamemode_label = make_label(f'Gamemode: {self.gamemode_list[self.gamemode]}')
        self.total_label = make_label(f'Money: {int(self.total)}')

        for i, label in enumerate([self.stake_label, self.gamemode_label, self.total_label]):
            anchor = UIAnchorLayout(width=SCREEN_WIDTH / 3, height=self._button_height)
            anchor.add(child=label, anchor_x="center", anchor_y="center")
            self.grid_top.add(child=anchor, column=i, row=0)

    def _show_steps(self) -> None:
        self.steps = []

        for i in range(MAX_STEPS):
            button = UITextureButton(texture=self.img, width=self._steps_width, height=self._steps_height)

            @button.event("on_click")
            def on_click(_, index=i):  # `index=i` closes over correct loop variable
                if self.stake == 0:
                    return
                self.steps[index].texture = self._show_alive_img()
                self.steps[index].text = ''
                self.steps[index].disabled = True
                self._toggle_input(False)
                if index + 1 < len(self.steps):
                    self.steps[index + 1].disabled = False
                self.send_event(events.DoStep(stake=int(self.stake), take=int(self.take), step=index))
                self.on_draw()

            self.steps.append(button)
            self.grid_mid.add(child=button, column=i, row=0)
            self.send_event(events.UpdateMultiplier(multiplier=self.multiplier, step_text=i))

        self.street_img = arcade.gui.UIImage(texture=self.street_img)
        self.anchor_mid.add(child=self.street_img, anchor_x="center", anchor_y="center", index=0)

    def _show_buttons(self) -> None:
        def make_button(text: str, callback) -> UITextureButton:
            button = UITextureButton(
                texture=self.button_img,
                text=text,
                width=self._button_width,
                height=self._button_height,
            )

            @button.event("on_click")
            def handle_click(_: arcade.gui.UIOnClickEvent) -> None:
                callback()
            return button

        self.minus_button = make_button("-100", self.decrease_stake)
        self.plus_button = make_button("+100", self.increase_stake)
        self.diff_easy_button = make_button("Easy", lambda: self.set_gamemode(0))
        self.diff_mid_button = make_button("Medium", lambda: self.set_gamemode(1))
        self.diff_hard_button = make_button("Hard", lambda: self.set_gamemode(2))
        self.take_button = make_button(f"Take: {self.take}", self.take_money)

        for i, button in enumerate([
            self.minus_button, self.plus_button,
            self.diff_easy_button, self.diff_mid_button, self.diff_hard_button,
            self.take_button
        ]):
            self.grid_bottom.add(child=button, column=i, row=0)

    def _toggle_input(self, enabled: bool) -> None:
        self.plus_button.disabled = not enabled
        self.minus_button.disabled = not enabled
        self.diff_easy_button.disabled = not enabled
        self.diff_mid_button.disabled = not enabled
        self.diff_hard_button.disabled = not enabled

    def decrease_stake(self) -> None:
        if self.stake >= STAKE_STEP:
            self.stake -= STAKE_STEP
            self.total += STAKE_STEP
        self.refresh()

    def increase_stake(self) -> None:
        if self.total >= STAKE_STEP:
            self.total -= STAKE_STEP
            self.stake += STAKE_STEP
        self.refresh()

    def set_gamemode(self, mode: int) -> None:
        self.gamemode = mode
        self.send_event(events.UpdateGamemode(gamemode=mode))
        for i in range(MAX_STEPS):
            self.send_event(events.UpdateMultiplier(multiplier=self.multiplier, step_text=i))
        self.refresh()

    def take_money(self) -> None:
        for step in self.steps:
            step.texture = self.img
            step.visible = True
            step.disabled = True

        self.steps[0].disabled = False
        self.total += self.take
        self.take = 0
        self.stake = 0
        self.step = 1
        self._toggle_input(True)

        self.send_event(events.UpdateGamemode(gamemode=self.gamemode))
        self.send_event(events.UpdateTotal(total=self.total))
        for i in range(MAX_STEPS):
            self.send_event(events.UpdateMultiplier(multiplier=self.multiplier, step_text=i))

        self.refresh()

    @add_event_listener(events.UpdateMultiplierResponse)
    def show_multiplier(self, event: events.UpdateMultiplierResponse) -> None:
        self.multiplier = event.multiplier
        self.step_text = event.step_text
        self.steps[self.step_text].text = f'x{event.multiplier}'
        self.refresh()

    @add_event_listener(events.DoStepResponse)
    def do_step(self, event: events.DoStepResponse) -> None:
        self.stake = event.take
        self.take = event.take

        if self.take == 0:
            self.take_money()
        else:
            if self.step > 1:
                self.steps[self.step - 2].visible = False
            self.step += 1
            self.take_button.text = f"Take: {self.take}"
            if self.step > MAX_STEPS:
                self.take_money()

        self.on_draw()

    @add_event_listener(events.UpdateMoney)
    def update_money(self, event: events.UpdateMoney) -> None:
        self.total = event.money
        self.refresh()

    def refresh(self) -> None:
        self.stake_label.text = f'Stake: {self.stake}'
        self.gamemode_label.text = f'Gamemode: {self.gamemode_list[self.gamemode]}'
        self.total_label.text = f'Money: {int(self.total)}'
        self.take_button.text = f"Take: {self.take}"

    def _show_alive_img(self) -> arcade.Texture:
        return arcade.load_texture(ALIVE_IMG_PATH)

    @property
    @typing.override
    def can_pause(self) -> bool:
        return True

    def on_draw(self) -> None:
        super().on_draw()
        self.ui.draw()

    def on_show_view(self) -> None:
        self.ui.enable()

    def on_hide_view(self) -> None:
        self.ui.disable()