import json
import os
import arcade
from arcade.gui import UIManager, UITextureButton
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from network.client import AsyncWebSocketClient
from models.time_message import TimeMessage, TimeMessageList

class LobbyView(arcade.View):
    def __init__(self, room_id=None, client: AsyncWebSocketClient = None,
                 players=None, leader=None):
        super().__init__()
        arcade.set_background_color((150, 49, 150))
        self.client = AsyncWebSocketClient('ws://localhost:8765') if client is None else client
        if client is None:
            self.client.start()
        self.room_id = room_id
        self.players = players if players else []
        self.leader = leader if leader is not None else (room_id is None)
        self.already_in_room = client is not None and room_id is not None and players is not None
        self.joined = self.already_in_room
        self.leaving_to_game = False

        self.start_button = arcade.load_texture('images/start_button.png')
        self.start_button_hover = arcade.load_texture('images/start_button_hover.png')
        self.multiplayer_bar = arcade.load_texture('images/multiplayer_bar.png')
        self.back_to_menu_button = arcade.load_texture('images/back_to_menu_button_multiplayer.png')
        self.back_to_menu_button_hover = arcade.load_texture('images/back_to_menu_button_multiplayer_hover.png')

        self.manager = UIManager(self.window)
        self.setup_ui()
        self.manager.enable()

        self.first_player_text = arcade.Text('Waiting...', color=arcade.color.WHITE,
                                             x=40, y=460, font_size=30)
        self.second_player_text = arcade.Text('', color=arcade.color.WHITE,
                                              x=40, y=350, font_size=30)

        self.time_messages = TimeMessageList()

    def get_player_name(self):
        try:
            with open('user_state.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('player_name', 'Unknown')
        except (FileNotFoundError, json.JSONDecodeError):
            return 'Unknown'

    def on_show_view(self):
        if self.already_in_room:
            self.update_player_texts()
            return
        player_name = self.get_player_name()
        if self.room_id is None:
            self.client.send({'action': 'create_room', 'player_name': player_name})
            self.leader = True
        else:
            self.client.send({'action': 'join_room', 'room_id': self.room_id, 'player_name': player_name})
            self.leader = False
        self.client.send({'action': 'get_rooms'})

    def on_update(self, delta_time):
        self.time_messages.update(delta_time)
        msgs = self.client.get_messages()
        for msg in msgs:
            t = msg.get('type')
            if t == 'room_created':
                self.room_id = msg['room_id']
                self.players = msg.get('players', [])
                self.joined = True
                self.update_player_texts()
            elif t == 'player_joined':
                self.players = msg.get('players', self.players)
                self.joined = True
                self.update_player_texts()
            elif t == 'player_left':
                self.players = msg.get('players', [])
                self.update_player_texts()
            elif t == 'game_started':
                self.leaving_to_game = True
                from views.multiplayer_view import MultiplayerView
                multiplayer_view = MultiplayerView(self.client, self.room_id, self.players, self.leader)
                self.window.show_view(multiplayer_view)
            elif t == 'game_message':
                print("Соперник:", msg['data'])
            elif t == 'error':
                self.time_messages.append(TimeMessage(str(msg.get('message'))))

    def update_player_texts(self):
        if len(self.players) >= 1:
            p1 = self.players[0]
            leader_mark = ' (Leader)' if p1.get('leader') else ''
            self.first_player_text.text = f"{p1['name']}{leader_mark}"
        else:
            self.first_player_text.text = 'Waiting...'
        if len(self.players) >= 2:
            p2 = self.players[1]
            leader_mark = ' (Leader)' if p2.get('leader') else ''
            self.second_player_text.text = f"{p2['name']}{leader_mark}"
        else:
            self.second_player_text.text = 'Ждём соперника...'

    def on_draw(self):
        self.clear()
        scale = 1
        arcade.draw_texture_rect(self.multiplayer_bar, arcade.rect.XYWH(300, 450, 600*scale, 300*scale))
        self.first_player_text.draw()
        self.second_player_text.draw()
        self.manager.draw()
        self.time_messages.draw()

    def setup_ui(self):
        layout = UIAnchorLayout()
        box = UIBoxLayout()
        start_button = UITextureButton(width=400, height=200,
                                       texture=self.start_button,
                                       texture_hovered=self.start_button_hover,
                                       texture_pressed=self.start_button_hover)
        start_button.on_click = self.on_start_click
        box.add(start_button)
        layout.add(box, anchor_x='center', anchor_y='bottom', align_y=50)
        self.manager.add(layout)

        layout = UIAnchorLayout()
        box = UIBoxLayout()
        leave_button = UITextureButton(width=60, height=60,
                                       texture=self.back_to_menu_button,
                                       texture_hovered=self.back_to_menu_button_hover,
                                       texture_pressed=self.back_to_menu_button_hover)
        leave_button.on_click = self.on_back_click
        box.add(leave_button)
        layout.add(box, anchor_x='right', anchor_y='top', align_y=-10, align_x=-20)
        self.manager.add(layout)

    def on_start_click(self, event):
        if len(self.players) != 2:
            self.time_messages.append(TimeMessage('Недостаточно игроков для старта'))
            return
        self.client.send({'action': 'start_game'})

    def on_back_click(self, event):
        self.client.send({'action': 'leave_room'})
        self.client.close()
        from views.lobbies_view import LobbiesView
        self.window.show_view(LobbiesView())

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        if self.joined:
            self.client.send({'action': 'message', 'data': 'Hello!'})
        else:
            print("Ещё не в комнате, подождите...")

    def on_hide_view(self):
        if not self.leaving_to_game:
            self.client.send({'action': 'leave_room'})
            self.client.close()