import json
import random
import arcade
from arcade.gui import UIManager, UITextureButton
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from network.client import AsyncWebSocketClient
from models.player import Player

class MultiplayerView(arcade.View):
    def __init__(self, client: AsyncWebSocketClient, room_id, players, leader):
        super().__init__()
        self.client = client
        self.room_id = room_id
        self.player_info = players
        self.leader = leader

        self.player = Player(random.randint(100, 500), random.randint(100, 300))
        self.opponent_player = Player(300, 300)

        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)
        self.player_list.append(self.opponent_player)

        self.other_players = arcade.SpriteList()
        self.other_players.append(self.opponent_player)

        self.is_game = True
        self.keys_pressed = []

        self.solo_play_bar = arcade.load_texture("images/solo_play_bar.png")
        self.leave_button = arcade.load_texture("images/leave_button.png")
        self.leave_button_hover = arcade.load_texture("images/leave_button_hover.png")

        self.physics_engine = arcade.PhysicsEngineSimple(self.player, self.other_players)

        self.manager = UIManager(self.window)
        self.setup_ui()
        self.manager.enable()

    def on_draw(self):
        self.clear()
        scale = 1
        arcade.draw_texture_rect(self.solo_play_bar, arcade.rect.XYWH(300, 540, 600 * scale, 120 * scale))
        self.manager.draw()
        self.player_list.draw()

    def on_show_view(self):
        pass

    def on_update(self, delta_time):
        self.physics_engine.update()
        for msg in self.client.get_messages():
            t = msg.get('type')
            if t == 'opponent_position':
                self.opponent_player.center_x = msg['position']['x']
                self.opponent_player.center_y = msg['position']['y']
            elif t == 'return_to_menu':
                from views.menu_view import MenuView
                self.window.show_view(MenuView())
            elif t == 'player_left':
                if self.leader:
                    from views.lobby_view import LobbyView
                    lobby_view = LobbyView(client=self.client, room_id=self.room_id,
                                           players=msg.get('players', []), leader=True)
                    self.window.show_view(lobby_view)

        if self.is_game:
            self.client.send({'action': 'send_position', 'position': {'x': self.player.center_x, 'y': self.player.center_y}})

            vel_x, vel_y = 0.0, 0.0
            if arcade.key.W in self.keys_pressed or arcade.key.UP in self.keys_pressed:
                vel_y += self.player.speed * delta_time
            if arcade.key.A in self.keys_pressed or arcade.key.LEFT in self.keys_pressed:
                vel_x -= self.player.speed * delta_time
            if arcade.key.D in self.keys_pressed or arcade.key.RIGHT in self.keys_pressed:
                vel_x += self.player.speed * delta_time
            if arcade.key.S in self.keys_pressed or arcade.key.DOWN in self.keys_pressed:
                vel_y -= self.player.speed * delta_time

            if vel_x != 0 and vel_y != 0:
                factor = 0.7071
                vel_x *= factor
                vel_y *= factor

            self.player.move(vel_x, vel_y)
            self.player.center_x = max(25, min(self.player.center_x, 575))
            self.player.center_y = max(25, min(self.player.center_y, 455))

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        self.keys_pressed.append(symbol)

    def on_key_release(self, symbol: int, modifiers: int) -> bool | None:
        if symbol in self.keys_pressed:
            self.keys_pressed.remove(symbol)

    def setup_ui(self):
        layout = UIAnchorLayout()
        box = UIBoxLayout()
        button = UITextureButton(width=100, height=100,
                                 texture=self.leave_button,
                                 texture_hovered=self.leave_button_hover,
                                 texture_pressed=self.leave_button_hover)
        button.on_click = self.back_to_lobby
        box.add(button)
        layout.add(box, anchor_x='left', anchor_y='top', align_x=20, align_y=-20)
        self.manager.add(layout)

    def back_to_lobby(self, event):
        self.client.send({'action': 'leave_game'})