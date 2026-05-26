import arcade
from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from views.menu_view import MenuView


class Game(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, 'StepColor')
        menu_view = MenuView()
        self.show_view(menu_view)
        pass


    def on_update(self, delta_time: float) -> bool | None:
        pass


if __name__ == '__main__':
    game = Game()
    game.run()