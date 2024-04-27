import random
import mesa

# 1 tick is a week

class Bank(mesa.Agent):
    money = 500
    loan_ticks = 8
    loan_info = []

    compound_interval = 4

    def __init__(self, unique_id, model, annual_interest_rate):
        super().__init__(unique_id, model)
        self.annual_interest_rate = annual_interest_rate

    def loan(self, household, amount):
        household.cash += amount
        self.money -= amount
        self.loan_info.append({
            "household": household,
            "weeks": 0,
            "amount": amount
        })

    def demand_loan(self, info):
        if info["amount"] <= info["household"].cash:
            self.money += info["amount"]
            info["household"].cash -= info["amount"]
        else:
            self.money += info["household"].cash
            info["household"].cash = 0
            print(f"household {info['household'].unique_id} defaulted on loan of {info['amount']}")
            
        self.loan_info.remove(info)


    def step(self):
        for info in self.loan_info:
            info["weeks"] += 1
            if info["weeks"] % self.compound_interval == 0:
                info["amount"] *= 1 + self.annual_interest_rate / 12
            if info["weeks"] > self.loan_ticks:
                self.demand_loan(info)

    
class Household(mesa.Agent):
    cash = 20
    deposit = 0
    counter = 0
    rent_interval = 4
    strategy = "rent"
    strategy_start = 0

    def __init__(self, unique_id, model, bank, house_cost, utilities_cost, rent, income):
        super().__init__(unique_id, model)

        self.house_cost = house_cost
        self.utilities = utilities_cost
        self.rent = rent
        self.income = income

        self.model = model # isnt used right now
        self.bank = bank

    def step(self):
        if self.strategy == "rent" and (self.counter - self.strategy_start) % self.rent_interval == 0:
            self.bank.money += self.rent
            self.cash -= self.rent

        if self.cash < 15:
            needed_cash = 15 - self.cash

            if self.bank.money >= needed_cash:
                self.bank.loan(self, needed_cash)

        self.counter += 1

class Firm(mesa.Agent):
    pass
