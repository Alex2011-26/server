import json
import arcade
from arcade.color import ORANGE
from arcade.gui import UIManager, UITextureButton, UIInputText
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from constants import BLUE, BLACK, BROWN, RED, PURPLE, YELLOW, GREEN
from network.client import AsyncWebSocketClient

colors = [BLUE, BLACK, BROWN, RED, PURPLE, YELLOW, GREEN]


class LobbyView(arcade.View):
    def __init__(self, room_id=None):
        super().__init__()
        arcade.set_background_color((150, 49, 150))
        self.client = AsyncWebSocketClient('ws://localhost:8765')
        self.client.start()
        self.room_id = room_id
        self.joined = False

        self.start_button = arcade.load_texture('images/start_button.png')
        self.start_button_hover = arcade.load_texture('images/start_button_hover.png')
        self.multiplayer_bar = arcade.load_texture('images/multiplayer_bar.png')

        self.manager = UIManager(self.window)
        self.setup_ui()
        self.manager.enable()

        self.first_player_text = arcade.Text('First Player', color=arcade.color.WHITE, x=20, y=440, font_size=50)
        self.second_player_text = arcade.Text('Second Player', color=arcade.color.WHITE, x=20, y=330, font_size=50)

    def on_draw(self) -> bool | None:
        self.clear()
        scale = 1
        arcade.draw_texture_rect(self.multiplayer_bar, arcade.rect.XYWH(300, 450, 600*scale, 300*scale))
        self.first_player_text.draw()
        self.second_player_text.draw()
        self.manager.draw()

    def on_show_view(self):
        if self.room_id is None:
            self.client.send({'action': 'create_room'})
        else:
            self.client.send({'action': 'join_room', 'room_id': self.room_id})
        self.client.send({'action': 'get_rooms'})

    def on_update(self, delta_time):
        msgs = self.client.get_messages()
        for msg in msgs:
            t = msg.get('type')
            if t == 'room_created':
                self.room_id = msg['room_id']
                self.joined = True
                print(f"Комната создана, ID: {msg['room_id']}")
            elif t == 'player_joined':
                print(f"Игроков в комнате: {msg['count']}")
                self.joined = True
            elif t == 'send_rooms':
                print(msg['rooms'])
            elif t == 'game_message':
                print("Соперник:", msg['data'])
            elif t == 'error':
                print("Ошибка:", msg.get('message'))

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        if self.joined:
            self.client.send({'action': 'message', 'data': 'Hello!'})
        else:
            print("Ещё не в комнате, подождите...")

    def setup_ui(self):
        layout = UIAnchorLayout()
        box = UIBoxLayout()
        start_button = UITextureButton(width=400, height=200,
                                       texture=self.start_button,
                                       texture_hovered=self.start_button_hover,
                                       texture_pressed=self.start_button_hover)

        box.add(start_button)
        layout.add(box, anchor_x='center', anchor_y='bottom', align_y=50)
        self.manager.add(layout)
