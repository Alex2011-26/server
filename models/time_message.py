from models.timer import Timer
import arcade


class TimeMessage:
    def __init__(self, message):
        self.message = arcade.Text(str(message), font_size=20, color=arcade.color.RED, x=0, y=550)
        self.message.x = 300 - self.message.content_width // 2
        self.timer = Timer(2)

    def update(self, dt):
        self.timer.update(dt)
        if self.timer.check()[0]:
            self.message.draw()


class TimeMessageList:
    def __init__(self):
        self.messages = []

    def append(self, message):
        self.messages.append(message)

    def update(self, dt):
        for message in self.messages:
            message.update(dt)
            if not(message.timer.check()[0]):
                self.messages.remove(message)

    def draw(self):
        for message in self.messages:
            if message.timer.check()[0]:
                message.message.draw()
