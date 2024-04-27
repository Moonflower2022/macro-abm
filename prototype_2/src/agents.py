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

class Bank(mesa.Agent):
    money = 500
    loan_ticks = 8
    loan_info = []

    compound_interval = 4

    def __init__(self, unique_id, model, annual_interest_rate):
        super().__init__(unique_id, model)
        self.annual_interest_rate = annual_interest_rate

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
    deposit = 0
    counter = 0
    rent_interval = 4
    strategy = "rent"
    strategy_start = 0

    def __init__(self, unique_id, model, house_cost, utilities_cost, rent, income):
        super().__init__(unique_id, model)

        self.house_cost = house_cost
        self.utilities = utilities_cost
        self.rent = rent
        self.income = income

        self.model = model # isnt used right now
        self.bank = find(model, Bank)

    def step(self):
        if self.strategy == "rent" and (self.counter - self.strategy_start) % self.rent_interval == 0:
            self.bank.money += self.rent
            self.money -= self.rent

        if self.money < 15:
            needed_money = 15 - self.money

            if self.bank.money >= needed_money:
                self.bank.loan(self, needed_money)

        self.counter += 1

class Firm(mesa.Agent):



    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

