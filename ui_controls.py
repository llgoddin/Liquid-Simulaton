"""Small, time-based controls for the interactive simulator."""


class CountRepeater:
    """One immediate change, then a smoothly accelerating, bounded hold repeat.

    The initial delay is 0.4 seconds. Subsequent intervals decline smoothly
    from 0.32 seconds towards a floor of 0.06 seconds as the hold continues.
    """

    def __init__(self):
        self.action = None
        self.started = 0.0
        self.next_time = 0.0

    def press(self, action, now):
        self.action = action
        self.started = now
        self.next_time = now + 0.4
        return 1

    def release(self):
        self.action = None

    def update(self, now):
        if self.action is None:
            return 0
        count = 0
        while now >= self.next_time and count < 200:
            elapsed = self.next_time - self.started
            self.next_time += max(0.06, 0.32 / (1 + 0.7 * elapsed))
            count += 1
        return count
