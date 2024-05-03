import mesa
from .utils import get, get_all, time_due
import random

# 1 tick is a week

class Bank(mesa.Agent):
    money = 500
    loan_ticks = 8
    loan_info = []
    deposits = {}

    monthly_interest_rate = 0.005
    compound_interval = 4

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def loan(self, household, amount):
        household.money += amount
        self.money -= amount
        self.loan_info.append({
            "household": household,
            "weeks": 0,
            "amount": amount
        })

    def demand_loan(self, info):
        if info["amount"] <= self.deposits[info["household"].unique_id]["amount"]:
            self.money += info["amount"]
            self.deposits[info["household"].unique_id]["amount"] -= info["amount"]
        elif info["amount"] <= info["household"].money:
            self.money += info["amount"]
            info["household"].money -= info["amount"]
        else:
            print(f"household {info['household'].unique_id} defaulted on loan of {info['amount']}, could only pay back {info['household'].money}")
            self.money += info["household"].money
            info["household"].money = 0
            
        self.loan_info.remove(info)

    def deposit(self, household, amount):
        if household.unique_id in self.deposits:
            self.deposits[household.unique_id]["amount"] += amount
            household.money -= amount
        else:
            self.deposits[household.unique_id] = {
                "amount": amount,
                "start": household.model.schedule.time
            }

    def withdraw(self, household, amount):
        if household.unique_id in self.deposits:
            if amount == "all":
                household.money += self.deposits[household.unique_id]["amount"]
                self.deposits[household.unique_id]["amount"] = 0
                return
            if amount < self.deposits[household.unique_id]["amount"]:
                household.money += amount
                self.deposits[household.unique_id]["amount"] -= amount
                return
            raise Exception("household is withdrawing more money than it can")                
        raise Exception("household is trying to withdraw from bank when it doesnt have any deposit money in its name")
        

    def step(self):
        for info in self.loan_info:
            info["weeks"] += 1
            if info["weeks"] % self.compound_interval == 0:
                info["amount"] *= 1 + self.monthly_interest_rate
            if info["weeks"] > self.loan_ticks:
                self.demand_loan(info)
        for info in self.deposits.values():
            if time_due(self.model, info["start"], self.compound_interval):
                compound_addition = info["amount"] * self.monthly_interest_rate
                if self.money > compound_addition:
                    self.money -= compound_addition
                    info["amount"] += compound_addition
                else:
                    raise Exception("bank defaulted :(")
                

class Household(mesa.Agent):
    money = 20
    goods = 3
    
    rent_interval = 4
    mortgage_interval = 4
    utilities_interval = 4

    strategy = "rent"
    strategy_start = 0

    house_cost = 360
    rent = 15
    utilities_cost = rent / 5
    mortgage_cost = 30
    weekly_goods_consumption = 3
    weekly_goods_consumption_range = 0.25
    monthly_morgage_rate = 0.035

    def __init__(self, unique_id, model, income, education):
        super().__init__(unique_id, model)
        self.income = income # maybe delete
        self.education = education

        self.model = model
        
    def get_references(self):
        self.bank = get(self.model, Bank)
        self.government = get(self.model, Government)

    def consume(self):
        lower_bound = self.weekly_goods_consumption - self.weekly_goods_consumption_range
        upper_bound = self.weekly_goods_consumption + self.weekly_goods_consumption_range
        self.goods -= random.uniform(lower_bound, upper_bound)

    def pay_rent(self):
        self.money -= self.rent
        self.bank.money += self.rent - self.utilities_cost
        # bank should pay 20% of the rent to the government
        self.government.money += self.utilities_cost

    def pay_utilities(self):
        self.money -= self.utilities_cost
        self.government.money += self.utilities_cost
        
    def pay_mortgage(self):
        mortgage_after_interest = self.mortgage_cost * (1 + self.monthly_morgage_rate) ** ((self.model.schedule.time - self.strategy_start) / 4)
        self.money -= mortgage_after_interest
        self.bank.money += mortgage_after_interest - self.utilities_cost
        self.government.money += self.utilities_cost

    def buy_house(self):
        self.bank.withdraw(self, "all")
        if self.money >= 360:
            self.strategy = "own house"
            self.money -= 360
        elif self.money >= 270:
            self.strategy = "mortgage A"
            self.money -= 270
        elif self.money >= 180:
            self.strategy = "mortgage B"
            self.money -= 180
        elif self.money >= 90:
            self.strategy = "mortgage C"
            self.money -= 90
        else:
            raise Exception("household agent does not have enough money to buy house :(")
        self.strategy_start = self.model.schedule.time

    def step(self):
        if self.model.schedule.time == 0:
            self.get_references()
        self.consume()
        self.goods += 3.5

        if self.strategy == "rent" and time_due(self.model, self.strategy_start, self.rent_interval):
            self.pay_rent()

        if self.strategy[:8] == "mortgage" and time_due(self.model, self.strategy_start, self.mortgage_interval):
            self.pay_mortgage()

        if self.strategy == "own house" and time_due(self.model, self.strategy_start, self.utilities_interval):
            self.pay_utilities()

        if self.strategy[:8] == "mortgage":
            if (self.model.schedule.time - self.strategy_start) / 4 >= {"A": 3, "B": 6, "C": 9}[self.strategy[9]]:
                self.strategy = "own house"
                self.strategy_start = self.model.schedule.time

        if self.money > 15 and self.strategy == "rent":
            self.bank.deposit(self, self.money - 15)

        elif self.money > 40 and (self.strategy[:8] == "mortgage" or self.strategy == "own house"):
            self.bank.deposit(self, self.money - 40)

        if self.money < 15:
            needed_money = 15 - self.money

            if self.bank.money >= needed_money:
                self.bank.loan(self, needed_money)

        if self.model.schedule.time == 14 * 4: # 14 months
            self.buy_house()
            
class Government(mesa.Agent):
    money = 500

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)


class Firm(mesa.Agent):
    money = 2000
    goods = 0
    employees = [0, 0, 0]

    goods_cost = 5

    goods_interval = 1

    def __init__(self, unique_id, model, required_employees):
        super().__init__(unique_id, model)
        self.required_employees = required_employees

    def fraction_production(self):
        number_required = len(self.required_employees) - self.required_employees.count(0)
        fraction = 0

        for i, requirement in enumerate(self.required_employees):
            if not requirement == 0:
                fraction += self.employees[i] / requirement

        return fraction / number_required

    def get_references(self):
        self.households = get_all(self.model, Household)

    def pay_wages(self): # old
        for household in self.households:
            household.money += household.income
            if self.money < household.income:
                raise Exception("firm just defaulted??!?!?!?!?!")
            self.money -= household.income

    def export_goods(self): # old
        self.money += 2000

    def sell_goods(self): # old
        for household in self.households:
            household.money -= self.goods_cost
            self.money += self.goods_cost

    def step(self): # old
        if self.model.schedule.time == 0:
            self.get_references()

        if time_due(self.model, 0, self.goods_interval):
            self.pay_wages()
            self.export_goods()
            self.sell_goods()

class LargeFirm(Firm):

    def __init__(self, unique_id, model, required_employees):
        super().__init__(self, unique_id, model, required_employees)

class MediumFirm(Firm):

    def __init__(self, unique_id, model, required_employees):
        super().__init__(self, unique_id, model, required_employees)

class SmallFirm(Firm):

    def __init__(self, unique_id, model, required_employees):
        super().__init__(self, unique_id, model, required_employees)

