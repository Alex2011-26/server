import random
import arcade
from arcade.gui import UIManager, UITextureButton
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from constants import BLUE, BLACK, BROWN, RED, PURPLE, YELLOW, GREEN
from models.player import Player
from models.timer import Timer, TimerList

colors = [BLUE, BLACK, BROWN, RED, PURPLE, YELLOW, GREEN]


class SoloPlayView(arcade.View):
    def __init__(self):
        super().__init__()
        self.back_pattern = self.generate_back_pattern()
        self.update_back_pattern_timer = 0

        self.solo_play_bar = arcade.load_texture("images/solo_play_bar.png")
        self.pause_button = arcade.load_texture("images/pause_button.png")
        self.pause_button_hover = arcade.load_texture("images/pause_button_hover.png")
        self.game_over_modal = arcade.load_texture("images/game_over_modal.png")
        self.pause_modal = arcade.load_texture("images/pause_modal.png")
        self.restart_button = arcade.load_texture("images/restart_button.png")
        self.restart_button_hover = arcade.load_texture("images/restart_button_hover.png")
        self.continue_button = arcade.load_texture("images/continue_button.png")
        self.continue_button_hover = arcade.load_texture("images/continue_button_hover.png")
        self.leave_button = arcade.load_texture("images/leave_button.png")
        self.leave_button_hover = arcade.load_texture("images/leave_button_hover.png")

        self.score = 0
        self.score_text = str(self.score)
        self.is_game = True
        self.is_pause = False

        self.setup_ui()

        self.player = Player(300, 240)
        self.players = arcade.SpriteList()
        self.players.append(self.player)

        self.keys_pressed = []

        self.countdown_timer = Timer(3)
        self.go_to_color_timer = Timer(2)

        self.color_to_stay = None

    def generate_back_pattern(self):
        rows = 10
        cols = 8
        total_cells = rows * cols
        target = {c: 11 for c in colors}
        extra_colors = random.sample(colors, 3)
        for c in extra_colors:
            target[c] += 1  # теперь сумма 80

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

        for ind_x, x in enumerate(self.back_pattern):
            for ind_y, y in enumerate(x):
                arcade.draw_lbwh_rectangle_filled(60 * ind_x, 60 * ind_y, 60, 60, y)

        scale = 1
        arcade.draw_texture_rect(self.solo_play_bar, arcade.rect.XYWH(300, 540, 600*scale, 120 * scale))
        if self.color_to_stay:
            arcade.draw_lbwh_rectangle_filled(280, 520, 40, 40, self.color_to_stay)
            arcade.draw_lbwh_rectangle_outline(278, 518, 42, 42, arcade.color.BLACK, 4)
        self.manager.draw()

        text_score = f'{''.join(list(['0' for _ in range(4 - len(str(self.score)))]))}{self.score}'
        self.score_text = text_score

        x = 461

        for char in self.score_text:
            arcade.draw_text(
                char, x, 570,
                arcade.color.ORANGE, 40,
                anchor_x="left", anchor_y="top", bold=True
            )
            text_obj = arcade.Text(char, 0, 0, font_size=40, bold=True)
            char_width = text_obj.content_width
            x += char_width + 4

        self.players.draw()

        if not self.is_game:
            scale = 1
            arcade.draw_texture_rect(self.game_over_modal, arcade.rect.XYWH(300, 300, 400 * scale, 400 * scale))
            self.game_over_manager.draw()

            score_text = arcade.Text(f"{self.score}!", 230, 180, font_size=40, bold=True, color=arcade.color.ORANGE)
            score_text.draw()

        if self.is_pause:
            scale = 1
            arcade.draw_texture_rect(self.pause_modal, arcade.rect.XYWH(300, 300, 400 * scale, 400 * scale))
            self.pause_manager.draw()

    def on_update(self, delta_time: float) -> bool | None:
        if self.is_game and not self.is_pause:
            self.countdown_timer.update(delta_time)
            vel_x, vel_y = 0, 0
            if arcade.key.W in self.keys_pressed or arcade.key.UP in self.keys_pressed:
                vel_y += self.player.speed * delta_time
            if arcade.key.A in self.keys_pressed or arcade.key.LEFT in self.keys_pressed:
                vel_x -= self.player.speed * delta_time
            if arcade.key.D in self.keys_pressed or arcade.key.RIGHT in self.keys_pressed:
                vel_x += self.player.speed * delta_time
            if arcade.key.S in self.keys_pressed or arcade.key.DOWN in self.keys_pressed:
                vel_y -= self.player.speed * delta_time

            if vel_x != 0 and vel_y != 0:
                factor = 0.7071  # ≈ 1/√2
                vel_x *= factor
                vel_y *= factor

            self.player.move(vel_x, vel_y)

            if self.countdown_timer.check()[0]:
                self.back_pattern = self.generate_back_pattern()
                self.color_to_stay = random.choice(colors)
            else:
                if self.go_to_color_timer.check()[0]:
                    print(self.color_to_stay)
                    self.go_to_color_timer.update(delta_time)
                else:
                    x = self.player.center_x // 60 - 1 if self.player.center_x % 60 == 0 else self.player.center_x // 60
                    y = self.player.center_y // 60 - 1 if self.player.center_y % 60 == 0 else self.player.center_y // 60
                    color = self.back_pattern[int(x)][int(y)]
                    if color == self.color_to_stay:
                        self.score += 1
                        self.countdown_timer.reset()
                        self.go_to_color_timer.reset()
                        self.go_to_color_timer.change_time(self.go_to_color_timer.time * 0.99)
                    else:
                        self.manager.disable()
                        self.game_over_manager.enable()
                        self.is_game = False

    def on_pause_click(self, event):
        if not self.is_game:
            return
        self.is_pause = True
        self.manager.disable()
        self.pause_manager.enable()

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        self.keys_pressed.append(symbol)
        if symbol == arcade.key.ESCAPE:
            self.on_pause_click(None)

    def on_key_release(self, symbol: int, modifiers: int) -> bool | None:
        self.keys_pressed.remove(symbol)

    def restart(self, event):
        self.game_over_manager.disable()
        self.pause_manager.disable()
        self.manager.enable()

        self.countdown_timer = Timer(3)
        self.go_to_color_timer = Timer(2)
        self.is_game = True
        self.is_pause = False
        self.score = 0
        self.score_text = str(self.score)

        self.player = Player(300, 240)
        self.players = arcade.SpriteList()
        self.players.append(self.player)

    def continue_game(self, event):
        self.is_pause = False

        self.pause_manager.disable()
        self.game_over_manager.disable()
        self.manager.enable()

    def leave_to_menu(self, event):
        from views.menu_view import MenuView
        menu_view = MenuView()
        self.window.show_view(menu_view)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        if self.pause_manager.enabled:
            self.pause_manager.on_mouse_motion(x, y, dx, dy)
        elif self.game_over_manager.enabled:
            self.game_over_manager.on_mouse_motion(x, y, dx, dy)
        elif self.manager.enabled:
            self.manager.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if self.pause_manager.enabled:
            self.pause_manager.on_mouse_press(x, y, button, modifiers)
        elif self.game_over_manager.enabled:
            self.game_over_manager.on_mouse_press(x, y, button, modifiers)
        elif self.manager.enabled:
            self.manager.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if self.pause_manager.enabled:
            self.pause_manager.on_mouse_release(x, y, button, modifiers)
        elif self.game_over_manager.enabled:
            self.game_over_manager.on_mouse_release(x, y, button, modifiers)
        elif self.manager.enabled:
            self.manager.on_mouse_release(x, y, button, modifiers)

    def on_show_view(self):
        self.manager = UIManager(self.window)
        self.game_over_manager = UIManager(self.window)
        self.pause_manager = UIManager(self.window)

        self.setup_ui()

        self.manager.enable()

    def setup_ui(self):
        self.manager = UIManager(self.window)
        self.game_over_manager = UIManager(self.window)
        self.pause_manager = UIManager(self.window)

        self.manager.enable()
        self.anchor_layout = UIAnchorLayout()

        self.box_layout = UIBoxLayout(vertical=False, space_between=30)

        button = UITextureButton(width=80, height=80,
                                 texture=self.pause_button,
                                 texture_hovered=self.pause_button_hover,
                                 texture_pressed=self.pause_button_hover)

        button.on_click = self.on_pause_click
        self.box_layout.add(button)

        self.anchor_layout.add(self.box_layout, anchor_x='left', anchor_y='top', align_x=30, align_y=-20)
        self.manager.add(self.anchor_layout)

        self.game_over_anchor_layout = UIAnchorLayout()
        self.game_over_box_layout = UIBoxLayout()
        button = UITextureButton(width=140, height=140,
                                 texture=self.restart_button,
                                 texture_hovered=self.restart_button_hover,
                                 texture_pressed=self.restart_button_hover)

        button.on_click = self.restart
        self.game_over_box_layout.add(button)
        self.game_over_anchor_layout.add(self.game_over_box_layout, anchor_x='left', anchor_y='top', align_x=357,
                                         align_y=-330)
        self.game_over_manager.add(self.game_over_anchor_layout)

        self.pause_anchor_layout = UIAnchorLayout()
        self.pause_box_layout = UIBoxLayout(vertical=False, space_between=60)
        self.pause_box_layout_leave = UIBoxLayout(vertical=False, space_between=60)

        button = UITextureButton(width=140, height=140,
                                 texture=self.restart_button,
                                 texture_hovered=self.restart_button_hover,
                                 texture_pressed=self.restart_button_hover)

        button.on_click = self.restart

        button1 = UITextureButton(width=140, height=140,
                                  texture=self.continue_button,
                                  texture_hovered=self.continue_button_hover,
                                  texture_pressed=self.continue_button_hover)

        button1.on_click = self.continue_game

        button2 = UITextureButton(width=140, height=140,
                                  texture=self.leave_button,
                                  texture_hovered=self.leave_button_hover,
                                  texture_pressed=self.leave_button_hover)

        button2.on_click = self.leave_to_menu

        self.pause_box_layout.add(button1)
        self.pause_box_layout.add(button)
        self.pause_box_layout_leave.add(button2)

        self.pause_anchor_layout.add(self.pause_box_layout, anchor_x='left', anchor_y='top', align_x=127, align_y=-330)
        self.pause_anchor_layout.add(self.pause_box_layout_leave, anchor_x='left', anchor_y='top', align_x=227,
                                     align_y=-130)
        self.pause_manager.add(self.pause_anchor_layout)