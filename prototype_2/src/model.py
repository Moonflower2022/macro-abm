import mesa
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from .agents import Household, Bank
import itertools

def get_bank_money(model):
    return sum(agent.money for agent in model.schedule.agents if isinstance(agent, Bank))

def get_hh_money(model):
    return sum(agent.money for agent in model.schedule.agents if isinstance(agent, Household))

class MacroModel(mesa.Model):
    agent_num = 4

    house_cost = 360
    rent = 20
    utilities_cost = 3
    goods_cost = 5
    incomes = [30, 35, 40]
    annual_interest_rate = 0.005
    annual_morgage_rate = 0.035

    def __init__(self, total_steps=100):
        super().__init__()

        self.total_steps = total_steps
        self.schedule = RandomActivation(self)

        id_giver = itertools.count(1)
        self.schedule.add(Bank(next(id_giver), self, self.annual_interest_rate))
        for i in range(3):
            self.schedule.add(Household(next(id_giver), self, self.house_cost, self.utilities_cost, self.rent, self.incomes[i]))

        # Data collector
        self.datacollector = DataCollector(
            {
                "Bank Money": get_bank_money, 
                "Total Household Money": get_hh_money,
                "Money 1": lambda model: sum(agent.money for agent in model.schedule.agents if isinstance(agent, Household) and agent.unique_id == 2),
                "Money 2": lambda model: sum(agent.money for agent in model.schedule.agents if isinstance(agent, Household) and agent.unique_id == 3),
                "Money 3": lambda model: sum(agent.money for agent in model.schedule.agents if isinstance(agent, Household) and agent.unique_id == 4),                
            }
        )
        self.datacollector.collect(self)

    def step(self):
        # tell all the agents in the model to run their step function
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)
        
    def run_model(self):
        for i in range(self.total_steps):
            self.step()