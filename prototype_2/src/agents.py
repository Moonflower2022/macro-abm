import random
import mesa

# 1 tick is a week

def get(model, agent_class):
    agents = []
    for agent in model.schedule.agents:
        if isinstance(agent, agent_class):
            agents.append(agent)

    if len(agents) > 1:
        print(f"Warning: there are multiple {agent_class.__name__} in this model")
        return agents
    elif len(agents) == 1:
        return agents[0]
    # len(agents) == 0
    raise Exception(f"uh oh none of agent {agent_class.__name__} found in model")

def time_due(model, start, interval):
    return (model.schedule.time - start) % interval == 0

class Bank(mesa.Agent):
    money = 500
    loan_ticks = 8
    loan_info = []

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
        if info["amount"] <= info["household"].money:
            self.money += info["amount"]
            info["household"].money -= info["amount"]
        else:
            print(f"household {info['household'].unique_id} defaulted on loan of {info['amount']}, could only pay back {info['household'].money}")
            self.money += info["household"].money
            info["household"].money = 0
            
        self.loan_info.remove(info)


    def step(self):
        for info in self.loan_info:
            info["weeks"] += 1
            if info["weeks"] % self.compound_interval == 0:
                info["amount"] *= 1 + self.monthly_interest_rate
            if info["weeks"] > self.loan_ticks:
                self.demand_loan(info)

    
class Household(mesa.Agent):
    money = 20
    
    rent_interval = 4
    mortgage_interval = 4
    utilities_interval = 4

    strategy = "rent"
    strategy_start = 0

    house_cost = 360
    rent = 15
    utilities_cost = rent / 5
    mortgage_cost = 30
    monthly_morgage_rate = 0.035

    def __init__(self, unique_id, model, income):
        super().__init__(unique_id, model)
        self.income = income

        self.model = model
        self.bank = get(model, Bank)
        self.government = get(model, Government)

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
    money = 150

    goods_cost = 5

    goods_interval = 2

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def pay_wages(self):
        for household in self.households:
            household.money += household.income
            if self.money < household.income:
                raise Exception("firm just defaulted??!?!?!?!?!")
            self.money -= household.income

    def export_goods(self):
        self.money += 150

    def sell_goods(self):
        for household in self.households:
            household.money -= self.goods_cost
            self.money += self.goods_cost

    def step(self):
        if self.model.schedule.time == 0:
            self.households = get(self.model, Household)

        if time_due(self.model, 0, self.goods_interval):
            self.pay_wages()
            self.export_goods()
            self.sell_goods()
        

