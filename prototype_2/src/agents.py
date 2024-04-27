import random
import mesa

# 1 tick is a week

def find(model, agent_class):
    agents = []
    for agent in model.schedule.agents:
        if isinstance(agent, agent_class):
            agents.append(agent)

    if len(agents) > 1:
        print(f"Warning: there are multiple {agent_class.__name__} in this model")
        return agents
    # len(banks) == 1
    return agents[0]

def time_due(counter, start, interval):
    return (counter - start) % interval == 0

class Bank(mesa.Agent):
    money = 500
    loan_ticks = 8
    loan_info = []

    annual_interest_rate = 0.005
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
                info["amount"] *= 1 + self.annual_interest_rate / 12
            if info["weeks"] > self.loan_ticks:
                self.demand_loan(info)

    
class Household(mesa.Agent):
    money = 20
    
    rent_interval = 4
    mortgage_interval = 4

    strategy = "rent"
    strategy_start = 0
    counter = 0

    house_cost = 360
    utilities_cost = 3
    rent = 20
    goods_cost = 5
    mortgage_cost = 30
    annual_morgage_rate = 0.035

    def __init__(self, unique_id, model, income):
        super().__init__(unique_id, model)
        self.income = income

        self.model = model
        self.bank = find(model, Bank)

    def step(self):
        if self.strategy == "rent" and time_due(self.counter, self.strategy_start, self.rent_interval):
            self.bank.money += self.rent
            self.money -= self.rent

        if self.strategy[:8] == "mortgage" and time_due(self.counter, self.strategy_start, self.mortgage_interval):
            self.money -= self.mortgage_cost * (1 + self.annual_morgage_rate) ** ((self.counter - self.strategy_start) / 4)

        if self.strategy == "own house":
            self.money -= self.utilities_cost

        if self.strategy[:8] == "mortgage":
            if (self.counter - self.strategy_start) / 4 >= {"A": 3, "B": 6, "C": 9}[self.strategy[9]]:
                self.strategy = "own house"
                self.strategy_start = self.counter

        if self.money < 15:
            needed_money = 15 - self.money

            if self.bank.money >= needed_money:
                self.bank.loan(self, needed_money)

        if self.counter == 14 * 4: # 14 months
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
            
            self.strategy_start = self.counter

        self.counter += 1

class Firm(mesa.Agent):



    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

