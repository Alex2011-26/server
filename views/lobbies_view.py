import json
import arcade
from arcade.gui import UIManager, UITextureButton, UILabel
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout
from arcade.gui.experimental import UIScrollArea
from arcade.gui.experimental.scroll_area import UIScrollBar
from network.client import AsyncWebSocketClient

class LobbiesView(arcade.View):
    def __init__(self):
        super().__init__()
        arcade.set_background_color((150, 49, 150))
        self.lobby_bar = arcade.load_texture('images/lobby_bar.png')
        self.create_lobby_button = arcade.load_texture('images/create_lobby_button.png')
        self.create_lobby_button_hover = arcade.load_texture('images/create_lobby_button_hover.png')
        self.back_to_menu_button = arcade.load_texture('images/back_to_menu_button_multiplayer.png')
        self.back_to_menu_button_hover = arcade.load_texture('images/back_to_menu_button_multiplayer_hover.png')
        self.lobby_card = arcade.load_texture('images/lobby_card.png')
        self.lobby_card_hover = arcade.load_texture('images/lobby_card_hover.png')

        self.client = AsyncWebSocketClient('ws://localhost:8765')
        self.client.start()

        self.manager = UIManager(self.window)
        self.setup_ui()
        self.manager.enable()

        self.rooms = []

        self.back_btn_x = 20 + 75
        self.back_btn_y = 20 + 75
        self.back_btn_width = 150
        self.back_btn_height = 150
        self.back_btn_hover = False

    def on_show_view(self):
        self.client.send({'action': 'get_rooms'})

    def on_draw(self):
        self.clear()
        scale = 1
        arcade.draw_texture_rect(self.lobby_bar, arcade.rect.XYWH(300, 300, 600 * scale, 600 * scale))
        self.manager.draw()
        btn_texture = self.back_to_menu_button if not self.back_btn_hover else self.back_to_menu_button_hover
        arcade.draw_texture_rect(
            btn_texture,
            arcade.rect.XYWH(self.back_btn_x, self.back_btn_y,
                             self.back_btn_width, self.back_btn_height)
        )

    def on_update(self, delta_time):
        for msg in self.client.get_messages():
            t = msg.get('type')
            if t == 'send_rooms':
                self.rooms = msg['rooms']
                self.populate_room_cards()
            elif t == 'room_added':
                self.rooms.append({'room_id': msg['room_id'], 'players': msg['players']})
                self.populate_room_cards()
            elif t == 'room_removed':
                self.rooms = [r for r in self.rooms if r['room_id'] != msg['room_id']]
                self.populate_room_cards()
            elif t == 'room_updated':
                for room in self.rooms:
                    if room['room_id'] == msg['room_id']:
                        room['players'] = msg['players']
                        break
                self.populate_room_cards()
            elif t == 'player_joined':
                print(f"Player joined room {msg['room_id']}: {msg['count']} players")

    def setup_ui(self):
        root = UIAnchorLayout()
        self.manager.add(root)

        create_btn = UITextureButton(
            width=180, height=80,
            texture=self.create_lobby_button,
            texture_hovered=self.create_lobby_button_hover,
            texture_pressed=self.create_lobby_button_hover
        )
        create_btn.on_click = self.on_create_lobby_click
        create_layout = UIBoxLayout()
        create_layout.add(create_btn)
        root.add(create_layout, anchor_x='right', anchor_y='top', align_x=-40, align_y=-30)

        self.room_list_layout = UIBoxLayout(vertical=True, space_between=10)

        scroll_box = UIBoxLayout(vertical=False, align='bottom', size_hint=(1, 0.73))
        root.add(scroll_box, anchor_x="center", anchor_y="bottom")

        self.scroll_area = scroll_box.add(UIScrollArea(size_hint=(1, 1)))
        self.scroll_area.add(self.room_list_layout)
        scroll_box.add(UIScrollBar(self.scroll_area))

    def populate_room_cards(self):
        self.room_list_layout.clear()

        def make_handler(rid):
            def handler(event):
                room = next((r for r in self.rooms if r['room_id'] == rid), None)
                if room and room['players'] >= 2:
                    print(f"Комната {rid} уже заполнена")
                    return
                print(f"Clicked room: {rid}")
                self.join_room_click(rid)

            return handler

        for room in self.rooms:
            room_id = room['room_id']
            players = room['players']
            card_btn = UITextureButton(
                width=600, height=150,
                texture=self.lobby_card,
                texture_pressed=self.lobby_card_hover,
            )
            card_btn.on_click = make_handler(room_id)

            inner_root = UIAnchorLayout()
            box = UIBoxLayout(vertical=False, space_between=30)
            label_id = UILabel(text=f'{room_id}', text_color=arcade.color.WHITE, font_size=30)
            label_players = UILabel(f'{players}/2', text_color=arcade.color.GREEN if players < 2 else arcade.color.RED,
                                    font_size=40)
            box.add(label_id)
            box.add(label_players)
            inner_root.add(box, anchor_x='right', anchor_y='center', align_x=-60)
            card_btn.add(inner_root)
            self.room_list_layout.add(card_btn)

    def on_mouse_motion(self, x, y, dx, dy):
        self.manager.on_mouse_motion(x, y, dx, dy)
        if (self.back_btn_x - self.back_btn_width/2 <= x <= self.back_btn_x + self.back_btn_width/2 and
            self.back_btn_y - self.back_btn_height/2 <= y <= self.back_btn_y + self.back_btn_height/2):
            self.back_btn_hover = True
        else:
            self.back_btn_hover = False

    def on_mouse_press(self, x, y, button, modifiers):
        if (self.back_btn_x - self.back_btn_width/2 <= x <= self.back_btn_x + self.back_btn_width/2 and
            self.back_btn_y - self.back_btn_height/2 <= y <= self.back_btn_y + self.back_btn_height/2):
            self.on_back_to_menu_click(None)
        else:
            self.manager.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        self.manager.on_mouse_release(x, y, button, modifiers)

    def on_create_lobby_click(self, event):
        from views.lobby_view import LobbyView
        self.manager.disable()
        self.window.show_view(LobbyView(room_id=None))

    def join_room_click(self, room_id):
        from views.lobby_view import LobbyView
        self.manager.disable()
        self.window.show_view(LobbyView(room_id=room_id))

    def on_back_to_menu_click(self, event):
        from views.menu_view import MenuView
        self.window.show_view(MenuView())

    def on_hide_view(self):
        self.client.close()