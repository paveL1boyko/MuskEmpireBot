class BetCounter:
    bet_steps_count = 7

    def __init__(self, obj):
        self.obj = obj

    def min_bet(self):
        multiplier = 2
        if self.obj.level < 3:
            multiplier = 5
        elif self.obj.level < 6:
            multiplier = 4
        elif self.obj.level < 10:
            multiplier = 3

        calculated_bet = self.smart_zero_round(self.obj.mph * multiplier / (self.bet_steps_count * 3))
        return calculated_bet or 100

    def max_bet(self):
        return self.min_bet() * self.bet_steps_count

    def smart_zero_round(self, amount: int):
        def round_to_nearest(value, base=100):
            return round(value / base) * base

        if amount < 100:
            return round_to_nearest(amount, 50)
        elif amount < 1000:
            return round_to_nearest(amount, 100)
        elif amount < 10000:
            return round_to_nearest(amount, 1000)
        elif amount < 100000:
            return round_to_nearest(amount, 10000)
        elif amount < 1000000:
            return round_to_nearest(amount, 100000)
        elif amount < 10000000:
            return round_to_nearest(amount, 1000000)
        elif amount < 100000000:
            return round_to_nearest(amount, 10000000)
        else:
            return round_to_nearest(amount, 1000)

    def calculate_bet(self) -> int:
        max_bet_ = self.max_bet()
        min_bet_ = self.min_bet()
        while max_bet_ > self.obj.balance:
            max_bet_ -= min_bet_
        return max_bet_
