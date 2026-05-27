class Timer:
    def __init__(self, time):
        self.time = time
        self.reset_time = time

    def update(self, time_delta):
        self.time -= time_delta

    def check(self):
        return (self.time > 0, self.time)

    def reset(self):
        self.time = self.reset_time

    def change_time(self, new_time):
        self.time = new_time
        self.reset_time = new_time


class TimerList:
    def __init__(self):
        self.timers = []

    def append(self, timer: Timer):
        self.timers.append(timer)

    def update(self, time_delta):
        for timer in self.timers:
            timer.update(time_delta)