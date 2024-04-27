import mesa
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from .agents import Household, Bank
import itertools

def get_money(model):
    return sum(agent.money for agent in model.schedule.agents if isinstance(agent, Bank))

def get_deposits(model):
    return sum(sum(deposit_info["amount"] for deposit_info in agent.deposits.values()) for agent in model.schedule.agents if isinstance(agent, Bank))

def get_cash(model):
    return sum(agent.cash for agent in model.schedule.agents if isinstance(agent, Household))

class MacroModel(mesa.Model):
    agent_num = 4
    annual_interest = 0.005

    def __init__(self, total_steps=100):
        super().__init__()

        self.total_steps = total_steps
        self.schedule = RandomActivation(self)

        id_giver = itertools.count(1)
        bank = Bank(next(id_giver), self, self.annual_interest)
        self.schedule.add(bank)
        for i in range(3):
            self.schedule.add(Household(next(id_giver), self, bank, 20, self.annual_interest))

        # Data collector
        self.datacollector = DataCollector(
            {
                "Bank Money": get_money, 
                "Total Deposits": get_deposits,
                "Total Cash": get_cash,
                "Cash 1": lambda model: sum(agent.cash for agent in model.schedule.agents if isinstance(agent, Household) and agent.unique_id == 2),
                "Cash 2": lambda model: sum(agent.cash for agent in model.schedule.agents if isinstance(agent, Household) and agent.unique_id == 3),
                "Cash 3": lambda model: sum(agent.cash for agent in model.schedule.agents if isinstance(agent, Household) and agent.unique_id == 4),                
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