import mesa
from mesa.time import BaseScheduler
from mesa.datacollection import DataCollector
from .agents import Household, Bank, Government, Firm
from .utils import get, get_all, avg
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
    household_num = 40

    educations = [3] * 4 + [2] * 11 + [1] * 25
    incomes = [40] * 4 + [35] * 11 + [30] * 25

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
            self.schedule.add(Household(household_id, self, self.incomes[i], self.educations[i]))

        data_collectors = {}

        unique_educations = list(set(self.educations))

        for level in unique_educations:
            data_collectors[f"Education {level} Avg Money"] = lambda model, level=level: avg([agent.money for agent in model.schedule.agents if isinstance(agent, Household) and agent.education == level])
            data_collectors[f"Education {level} Avg Goods"] = lambda model, level=level: avg([agent.goods for agent in model.schedule.agents if isinstance(agent, Household) and agent.education == level])

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
        for _ in range(self.total_steps):
            self.step()