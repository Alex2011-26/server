import random
import arcade
from arcade.gui import UIManager, UITextureButton
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from constants import BLUE, BLACK, BROWN, RED, PURPLE, YELLOW, GREEN
from views.solo_play_view import SoloPlayView
from views.profile_view import ProfileView
from views.lobbies_view import LobbiesView

colors = [BLUE, BLACK, BROWN, RED, PURPLE, YELLOW, GREEN]


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.back_pattern = self.generate_back_pattern()
        self.update_back_pattern_timer = 0
        self.logo = arcade.load_texture('images/logo.png')
        self.solo_play_button = arcade.load_texture('images/solo_play_button.png')
        self.solo_play_button_hover = arcade.load_texture('images/solo_play_button_hover.png')
        self.profile_button = arcade.load_texture("images/profile_button.png")
        self.profile_button_hover = arcade.load_texture("images/profile_button_hover.png")
        self.multiplayer_button = arcade.load_texture("images/multiplayer_button.png")
        self.multiplayer_button_hover = arcade.load_texture("images/multiplayer_button_hover.png")

        self.manager = UIManager()
        self.manager.enable()
        self.anchor_layout = UIAnchorLayout()
        self.box_layout = UIBoxLayout(vertical=True, space_between=30)
        self.right_layout = UIBoxLayout(vertical=True, space_between=30)

        solo_play_button = UITextureButton(width=315, height=100,
                                  texture=self.solo_play_button,
                                  texture_hovered=self.solo_play_button_hover,
                                  texture_pressed=self.solo_play_button_hover)

        solo_play_button.on_click = self.on_solo_play_click
        multiplayer_button = UITextureButton(width=310, height=100,
                                           texture=self.multiplayer_button,
                                           texture_hovered=self.multiplayer_button_hover,
                                           texture_pressed=self.multiplayer_button_hover)

        multiplayer_button.on_click = self.on_multiplayer_click
        self.box_layout.add(solo_play_button)
        self.box_layout.add(multiplayer_button)

        profile_button = UITextureButton(width=120, height=120,
                                         texture=self.profile_button,
                                         texture_hovered=self.profile_button_hover,
                                         texture_pressed=self.profile_button_hover
                                         )
        profile_button.on_click = self.on_profile_click
        self.right_layout.add(profile_button)

        self.anchor_layout.add(self.box_layout, anchor_y='top', align_y=-360)
        self.anchor_layout.add(self.right_layout, anchor_x='right', anchor_y='top', align_x=-20, align_y=-400)
        self.manager.add(self.anchor_layout)

    @staticmethod
    def generate_back_pattern():
        target = {c: 14 for c in colors}
        extra_colors = random.sample(colors, 2)
        for c in extra_colors:
            target[c] += 1

        grid = [[None for _ in range(10)] for _ in range(10)]
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
                    r, c = random.randrange(10), random.randrange(10)
                    if grid[r][c] is None:
                        grid[r][c] = color
                        front = set()
                        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < 10 and 0 <= nc < 10 and grid[nr][nc] is None:
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
                if 0 <= nr < 10 and 0 <= nc < 10 and grid[nr][nc] is None:
                    front.add((nr, nc))
            clusters[idx][1] = remaining
            if remaining <= 0:
                clusters.pop(idx)

        empty_cells = [(r, c) for r in range(10) for c in range(10) if grid[r][c] is None]
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

        scale = 1.75
        arcade.draw_texture_rect(self.logo, arcade.rect.XYWH(300, 430, 300*scale, 200*scale))
        self.manager.draw()

    def on_update(self, delta_time: float) -> bool | None:
        self.update_back_pattern_timer += delta_time
        if self.update_back_pattern_timer > 1.7:
            self.update_back_pattern_timer = 0
            self.back_pattern = self.generate_back_pattern()

    def on_solo_play_click(self, event):
        solo_play_view = SoloPlayView()
        self.window.show_view(solo_play_view)

    def on_multiplayer_click(self, event):
        multiplayer_view = LobbiesView()
        self.window.show_view(multiplayer_view)

    def on_profile_click(self, event):
        profile_view = ProfileView()
        self.window.show_view(profile_view)