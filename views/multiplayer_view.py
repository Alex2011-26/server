import json
import random
import arcade
from arcade.gui import UIManager, UITextureButton
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from constants import BLUE, BLACK, BROWN, RED, PURPLE, YELLOW, GREEN
from network.client import AsyncWebSocketClient
from models.player import Player
from models.timer import Timer

colors = [BLUE, BLACK, BROWN, RED, PURPLE, YELLOW, GREEN]

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

        self.is_game = True
        self.keys_pressed = []

        self.back_pattern = None
        self.color_to_stay = None
        self.countdown_timer = Timer(3)
        self.go_to_color_timer = Timer(2)

        self.solo_play_bar = arcade.load_texture("images/solo_play_bar.png")
        self.leave_button = arcade.load_texture("images/leave_button.png")
        self.leave_button_hover = arcade.load_texture("images/leave_button_hover.png")

        self.manager = UIManager(self.window)
        self.setup_ui()
        self.manager.enable()

    def on_show_view(self):
        if self.leader:
            self.back_pattern = self.generate_back_pattern()
            self.color_to_stay = random.choice(colors)
            self.client.send({
                'action': 'sync_field',
                'back_pattern': self.back_pattern,
                'color_to_stay': self.color_to_stay
            })

    @staticmethod
    def generate_back_pattern():
        rows = 10
        cols = 8
        target = {c: 11 for c in colors}
        extra_colors = random.sample(colors, 3)
        for c in extra_colors:
            target[c] += 1
        grid = [[None for _ in range(cols)] for _ in range(rows)]
        clusters = []
        for color, count in target.items():
            if count == 0:
                continue
            num = min(random.randint(1, 3), count)
            base = count // num
            rem = count % num
            amounts = [base] * num
            for i in range(rem):
                amounts[i] += 1
            for amt in amounts:
                for _ in range(100):
                    r = random.randrange(rows)
                    c = random.randrange(cols)
                    if grid[r][c] is None:
                        grid[r][c] = color
                        front = set()
                        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] is None:
                                front.add((nr, nc))
                        clusters.append([color, amt - 1, front])
                        break
        while clusters:
            idx = random.randrange(len(clusters))
            color, remaining, front = clusters[idx]
            if remaining <= 0 or not front:
                clusters.pop(idx)
                continue
            r, c = random.choice(list(front))
            grid[r][c] = color
            remaining -= 1
            front.discard((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] is None:
                    front.add((nr, nc))
            clusters[idx][1] = remaining
            if remaining <= 0:
                clusters.pop(idx)
        empty_cells = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] is None]
        for r, c in empty_cells:
            available = [col for col, cnt in target.items() if cnt > 0]
            if available:
                col = random.choice(available)
                grid[r][c] = col
                target[col] -= 1
            else:
                grid[r][c] = random.choice(colors)
        return grid

    def on_draw(self):
        self.clear()
        if self.back_pattern:
            for ind_x, row in enumerate(self.back_pattern):
                for ind_y, color in enumerate(row):
                    arcade.draw_lbwh_rectangle_filled(60 * ind_x, 60 * ind_y, 60, 60, color)
        scale = 1
        arcade.draw_texture_rect(self.solo_play_bar, arcade.rect.XYWH(300, 540, 600 * scale, 120 * scale))
        if self.color_to_stay:
            arcade.draw_lbwh_rectangle_filled(280, 520, 40, 40, self.color_to_stay)
            arcade.draw_lbwh_rectangle_outline(278, 518, 42, 42, arcade.color.BLACK, 4)
        self.manager.draw()
        self.player_list.draw()

    def on_update(self, delta_time):
        for msg in self.client.get_messages():
            t = msg.get('type')
            if t == 'opponent_position':
                self.opponent_player.center_x = msg['position']['x']
                self.opponent_player.center_y = msg['position']['y']
            elif t == 'field_update':
                self.back_pattern = msg['back_pattern']
                self.color_to_stay = msg['color_to_stay']
                self.countdown_timer.reset()
                self.go_to_color_timer.reset()
            elif t == 'return_to_lobby':
                from views.lobby_view import LobbyView
                lobby_view = LobbyView(client=self.client, room_id=self.room_id,
                                       players=self.player_info, leader=self.leader)
                self.window.show_view(lobby_view)
                return
            elif t == 'return_to_menu':
                from views.menu_view import MenuView
                self.window.show_view(MenuView())
                return
            elif t == 'player_left':
                if self.leader:
                    from views.lobby_view import LobbyView
                    lobby_view = LobbyView(client=self.client, room_id=self.room_id,
                                           players=msg.get('players', []), leader=True)
                    self.window.show_view(lobby_view)
                else:
                    from views.menu_view import MenuView
                    self.window.show_view(MenuView())
                return

        if not self.is_game:
            return

        if not self.back_pattern:
            return

        if self.leader:
            self.countdown_timer.update(delta_time)
            if self.countdown_timer.check()[0]:
                self.back_pattern = self.generate_back_pattern()
                self.color_to_stay = random.choice(colors)
                self.client.send({
                    'action': 'sync_field',
                    'back_pattern': self.back_pattern,
                    'color_to_stay': self.color_to_stay
                })
            else:
                if self.go_to_color_timer.check()[0]:
                    self.go_to_color_timer.update(delta_time)
                else:
                    self.check_player_color()

        self.client.send({
            'action': 'send_position',
            'position': {'x': self.player.center_x, 'y': self.player.center_y}
        })

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

    def check_player_color(self):
        x = int(self.player.center_x // 60)
        y = int(self.player.center_y // 60)
        if 0 <= y < len(self.back_pattern) and 0 <= x < len(self.back_pattern[0]):
            color = self.back_pattern[y][x]
            if color == self.color_to_stay:
                print(color, self.color_to_stay)
                self.countdown_timer.reset()
                self.go_to_color_timer.reset()
                self.go_to_color_timer.change_time(self.go_to_color_timer.time * 0.99)
            else:
                print(color, self.color_to_stay)
                self.client.send({'action': 'game_over'})
                self.is_game = False

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