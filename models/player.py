import arcade


class Player(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.center_x = x
        self.center_y = y

        self.texture = arcade.make_circle_texture(50, arcade.color.PINK)
        self.speed = 200

    def move(self, vel_x, vel_y):
        self.center_x += vel_x
        self.center_y += vel_y
