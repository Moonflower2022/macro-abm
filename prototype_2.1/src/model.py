import mesa
from mesa.time import BaseScheduler
from mesa.datacollection import DataCollector
from .agents import Household, Bank, Government, Firm
from .utils import get, get_all
import itertools

def get_bank_money(model):
    return get(model, Bank).money

def get_government_money(model):
    return get(model, Government).money

def get_firm_money(model):
    return get(model, Firm).money

def get_household_money(model):
    return sum(household.money for household in get_all(model, Household))

def get_household_deposits(model):
    return sum(info["amount"] for info in get(model, Bank).deposits.values())

class MacroModel(mesa.Model):
    household_num = 3

    household_incomes = [35, 40, 45]

    def __init__(self, total_steps=100):
        super().__init__()

        self.total_steps = total_steps
        self.schedule = BaseScheduler(self)

        id_giver = itertools.count(1)
        self.schedule.add(Government(next(id_giver), self))
        self.schedule.add(Bank(next(id_giver), self))
        self.schedule.add(Firm(next(id_giver), self))

        household_ids = []
        for i in range(self.household_num):
            household_id = next(id_giver)
            household_ids.append(household_id)
            self.schedule.add(Household(household_id, self, self.household_incomes[i]))

        data_collectors = {}

        for i, id in enumerate(household_ids):
            data_collectors[f"Household {i + 1} Money"] = lambda model, agent_id=id: sum(agent.money for agent in model.schedule.agents if isinstance(agent, Household) and agent.unique_id == agent_id)

        data_collectors.update({
            "Bank Money": get_bank_money, 
            "Firm Money": get_firm_money,
            "Government Money": get_government_money,
            "Total Household Money": get_household_money,
            "Total Household Deposits": get_household_deposits,
        })

        self.datacollector = DataCollector(data_collectors)
        self.datacollector.collect(self)

    def step(self):
        # tell all the agents in the model to run their step function
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)
        
    def run_model(self):
        for i in range(self.total_steps):
            self.step()