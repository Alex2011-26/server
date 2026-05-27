import json
import arcade
from arcade.color import ORANGE
from arcade.gui import UIManager, UITextureButton, UIInputText
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from constants import BLUE, BLACK, BROWN, RED, PURPLE, YELLOW, GREEN

colors = [BLUE, BLACK, BROWN, RED, PURPLE, YELLOW, GREEN]


class LobbiesView(arcade.View):
    def __init__(self):
        super().__init__()
        arcade.set_background_color((150, 49, 150))
        self.lobby_bar = arcade.load_texture('images/lobby_bar.png')
        self.create_lobby_button = arcade.load_texture('images/create_lobby_button.png')
        self.create_lobby_button_hover = arcade.load_texture('images/create_lobby_button_hover.png')

        self.manager = UIManager()
        self.setup_ui()
        self.manager.enable()

    def on_draw(self) -> bool | None:
        self.clear()
        scale = 1
        arcade.draw_texture_rect(self.lobby_bar, arcade.rect.XYWH(300, 300, 600 * scale, 600 * scale))

        self.manager.draw()

    def on_update(self, delta_time: float) -> bool | None:
        pass

    def setup_ui(self):
        self.anchor_layout = UIAnchorLayout()
        self.box_layout = UIBoxLayout()

        create_lobby_button = UITextureButton(width=180, height=80,
                                              texture=self.create_lobby_button,
                                              texture_hovered=self.create_lobby_button_hover,
                                              texture_pressed=self.create_lobby_button_hover)

        create_lobby_button.on_click = self.on_create_lobby_click
        self.box_layout.add(create_lobby_button)
        self.anchor_layout.add(self.box_layout, anchor_x='right', anchor_y='top', align_x=-40, align_y=-30)
        self.manager.add(self.anchor_layout)

    def on_create_lobby_click(self, event):
        pass
