import math


class Calculator:
    def get_price(self, data, level):
        return self.calculate_formula(data.priceFormula, level, data.priceBasic, data.priceFormulaK) if level else 0

    def get_profit(self, data, level):
        return (
            self.calculate_formula(data.profitFormula, level, data.profitBasic, data.priceFormulaK, data)
            if level
            else 0
        )

    def calculate_formula(self, formula, level, base_value, formula_coefficient, data=None):
        result = base_value
        if formula == "fnCompound":
            result = self.fn_compound(level, base_value, formula_coefficient)
        elif formula == "fnLogarithmic":
            result = self.fn_logarithmic(level, base_value)
        elif formula == "fnLinear":
            result = self.fn_linear(level, base_value)
        elif formula == "fnQuadratic":
            result = self.fn_quadratic(level, base_value)
        elif formula == "fnCubic":
            result = self.fn_cubic(level, base_value)
        elif formula == "fnExponential":
            result = self.fn_exponential(level, base_value, formula_coefficient)
        elif formula == "fnPayback":
            result = self.fn_payback(level, data)

        return self.smart_round(result)

    def smart_round(self, value):
        def round_to(value, factor=100):
            return round(value / factor) * factor

        if value < 50:
            return round(value)
        elif value < 100:
            return round_to(value, 5)
        elif value < 500:
            return round_to(value, 25)
        elif value < 1000:
            return round_to(value, 50)
        elif value < 5000:
            return round_to(value, 100)
        elif value < 10000:
            return round_to(value, 200)
        elif value < 100000:
            return round_to(value, 500)
        elif value < 500000:
            return round_to(value, 1000)
        elif value < 1000000:
            return round_to(value, 5000)
        elif value < 50000000:
            return round_to(value, 10000)
        elif value < 100000000:
            return round_to(value, 50000)
        else:
            return round_to(value, 100000)

    def fn_linear(self, level, base_value):
        return base_value * level

    def fn_quadratic(self, level, base_value):
        return base_value * level * level

    def fn_cubic(self, level, base_value):
        return base_value * level * level * level

    def fn_exponential(self, level, base_value, coefficient):
        return base_value * math.pow(coefficient / 10, level)

    def fn_logarithmic(self, level, base_value):
        return base_value * math.log2(level + 1)

    def fn_compound(self, level, base_value, coefficient):
        compound_rate = coefficient / 100
        return base_value * math.pow(1 + compound_rate, level - 1)

    def fn_payback(self, level, data):
        accumulated = [0]
        for current_level in range(1, level + 1):
            previous_accumulated = accumulated[current_level - 1]
            current_price = self.get_price(data, current_level)
            current_profit = data.profitBasic + data.profitFormulaK * (current_level - 1)
            smart_rounded_value = self.smart_round(previous_accumulated + current_price / current_profit)
            accumulated.append(smart_rounded_value)
        return accumulated[level]
