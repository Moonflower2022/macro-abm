import random
import mesa

# 1 tick is a week

class Bank(mesa.Agent):
    money = 500
    loan_ticks = 8
    loan_info = []
    pending_deposits = {}
    deposits = {}

    compound_interval = 4

    def __init__(self, unique_id, model, monthly_interest):
        super().__init__(unique_id, model)
        self.monthly_interest = monthly_interest

    def deposit(self, household, amount):
        if household.unique_id in self.deposits:
            self.deposits[household.unique_id]["amount"] += amount
            household.cash -= amount
        else:
            self.deposits[household.unique_id] = {
                "amount": amount,
                "weeks": 0
            }
        

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
                info["amount"] *= 1 + self.monthly_interest
            if info["weeks"] > self.loan_ticks:
                self.demand_loan(info)
        for info in self.deposits.values():
            info["weeks"] += 1
            if info["weeks"] % self.compound_interval == 0:
                compound_addition = info["amount"] * self.monthly_interest
                if self.money > compound_addition:
                    self.money -= compound_addition
                    info["amount"] += compound_addition

    
class Household(mesa.Agent):
    cash = 100
    deposit = 0
    change_interval = 4
    compound_interval = 4    

    def __init__(self, unique_id, model, bank, income, monthly_interest):
        super().__init__(unique_id, model)
        self.income = income
        self.bank = bank
        self.monthly_interest = monthly_interest

    def step(self):
        if self.model.schedule.time % self.change_interval == 0:
            self.cash += self.income
            self.cash -= random.randint(10, 30)

        if self.cash < 25:
            needed_cash = 30 - self.cash

            if self.bank.deposits[self.unique_id]["amount"] >= needed_cash:
                self.cash += needed_cash
                self.bank.deposits[self.unique_id]["amount"] -= needed_cash
                self.deposit -= needed_cash

            if self.bank.money >= needed_cash:
                self.bank.loan(self, needed_cash)

        if self.cash > 65:
            self.bank.deposit(self, self.cash - 65)