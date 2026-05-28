import json
import arcade
from arcade.color import ORANGE
from arcade.gui import UIManager, UITextureButton, UIInputText
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from constants import BLUE, BLACK, BROWN, RED, PURPLE, YELLOW, GREEN
from network.client import AsyncWebSocketClient

colors = [BLUE, BLACK, BROWN, RED, PURPLE, YELLOW, GREEN]


class MultiplayerView(arcade.View):
    def __init__(self, client, room_id, players):
        super().__init__()
        self.client = client
        self.room_id = room_id
        self.players = players

    def on_draw(self) -> bool | None:
        self.clear()

    def on_show_view(self):
        pass

    def on_update(self, delta_time):
        pass

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        pass