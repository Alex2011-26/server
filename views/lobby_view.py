import json
import arcade
from arcade.color import ORANGE
from arcade.gui import UIManager, UITextureButton, UIInputText
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from constants import BLUE, BLACK, BROWN, RED, PURPLE, YELLOW, GREEN
from network.client import AsyncWebSocketClient

colors = [BLUE, BLACK, BROWN, RED, PURPLE, YELLOW, GREEN]


class LobbyView(arcade.View):
    def __init__(self):
        super().__init__()
        arcade.set_background_color((150, 49, 150))
        self.client = AsyncWebSocketClient('ws://localhost:8765')
        self.client.start()

    def on_show_view(self):
        self.client.send({'action': 'create_room'})
        self.client.send({'action': 'get_rooms'})

    def on_update(self, delta_time):
        msgs = self.client.get_messages()
        for msg in msgs:
            if msg.get('type') == 'room_created':
                print(f"Комната создана, ID: {msg['room_id']}")
            elif msg.get('type') == 'player_joined':
                print(f"Игроков в комнате: {msg['count']}")
            elif msg.get('type') == 'send_rooms':
                print(msg['rooms'])
            else:
                print("Получено:", msg)

    def on_draw(self):
        self.clear()

    def on_hide_view(self) -> None:
        self.client.send({'action': 'leave_room'})
        self.client.close()

