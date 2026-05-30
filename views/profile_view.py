import json
import arcade
from arcade.color import ORANGE
from arcade.gui import UIManager, UITextureButton, UIInputText
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from constants import BLUE, BLACK, BROWN, RED, PURPLE, YELLOW, GREEN
from models.time_message import TimeMessage, TimeMessageList

colors = [BLUE, BLACK, BROWN, RED, PURPLE, YELLOW, GREEN]


class ProfileView(arcade.View):
    def __init__(self):
        super().__init__()

        self.background = arcade.load_texture('images/profile_stats.png')
        self.change_name = arcade.load_texture('images/change_name.png')
        self.change_name_hover = arcade.load_texture('images/change_name_hover.png')
        self.back_to_menu_button = arcade.load_texture('images/back_to_menu_button.png')
        self.back_to_menu_button_hover = arcade.load_texture('images/back_to_menu_button_hover.png')

        self.manager = UIManager()
        self.setup_ui()
        self.manager.enable()

        with open('user_state.json', 'r') as f:
            file = json.load(f)
        self.user_name = file['player_name']
        self.user_solo_highest_score = file['solo_highest_score']
        self.user_multiplayer_highest_score = file['multiplayer_highest_score']

        self.user_name_text = arcade.Text(self.user_name, 0,  540, (255, 200, 89), 30)
        self.user_name_text.x = 300 - self.user_name_text.content_width // 2

        self.user_solo_highest_score_text = arcade.Text(str(self.user_solo_highest_score), 250, 297, BLUE, 30)
        self.user_multiplayer_highest_score_text = arcade.Text(str(self.user_multiplayer_highest_score), 260, 207, BLUE, 30)

        self.time_message_list = TimeMessageList()

    def on_draw(self) -> bool | None:
        self.clear()
        scale = 1
        arcade.draw_texture_rect(self.background, arcade.rect.XYWH(300, 300, 600 * scale, 600 * scale))
        self.manager.draw()
        self.user_name_text.draw()
        self.user_solo_highest_score_text.draw()
        self.user_multiplayer_highest_score_text.draw()
        self.time_message_list.draw()

    def on_update(self, delta_time: float) -> bool | None:
        self.time_message_list.update(delta_time)

    def on_back_click(self, event):
        from views.menu_view import MenuView
        menu_view = MenuView()
        self.window.show_view(menu_view)

    def setup_ui(self):
        self.name_anchor_layout = UIAnchorLayout()
        self.menu_anchor_layout = UIAnchorLayout()
        self.change_name_layout = UIBoxLayout(vertical=True, space_between=30)
        self.back_to_menu_layout = UIBoxLayout()

        back_to_menu_button = UITextureButton(width=150, height=150,
                                              texture=self.back_to_menu_button,
                                              texture_hovered=self.back_to_menu_button_hover,
                                              texture_pressed=self.back_to_menu_button_hover)
        back_to_menu_button.on_click = self.on_back_click
        self.back_to_menu_layout.add(back_to_menu_button)
        self.menu_anchor_layout.add(self.back_to_menu_layout, anchor_x='left', anchor_y='bottom', align_y=30, align_x=50)

        change_name_button = UITextureButton(width=230, height=50,
                                             texture=self.change_name,
                                             texture_hovered=self.change_name_hover,
                                             texture_pressed=self.change_name_hover
                                             )
        change_name_button.on_click = self.change_name_func
        self.change_name_input = UIInputText(width=280, height=90, text_color=arcade.color.WHITE, border_width=0, font_size=40, border_color=ORANGE, text='...', caret_color=arcade.color.WHITE)
        self.change_name_layout.add(self.change_name_input)
        self.change_name_layout.add(change_name_button)
        self.name_anchor_layout.add(self.change_name_layout, anchor_x='left', anchor_y='top', align_y=-90, align_x=145)

        self.manager.add(self.menu_anchor_layout)
        self.manager.add(self.name_anchor_layout)

    def change_name_func(self, event):
        name = self.change_name_input.text
        if 4 <= len(name) <= 9:
            with open('user_state.json', 'r') as f:
                file = json.load(f)

            file['player_name'] = name
            json.dump(file, open('user_state.json', 'w'))

            with open('user_state.json', 'r') as f:
                file = json.load(f)

            self.user_name = file['player_name']
            self.user_solo_highest_score = file['solo_highest_score']
            self.user_multiplayer_highest_score = file['multiplayer_highest_score']

            self.user_name_text = arcade.Text(self.user_name, 0, 540, (255, 200, 89), 30)
            self.user_name_text.x = 300 - self.user_name_text.content_width // 2

        else:
            self.time_message_list.append(TimeMessage('Длина имени от 4 до 9 символов'))

