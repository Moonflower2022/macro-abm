import mesa
from mesa.time import BaseScheduler
from mesa.datacollection import DataCollector
from .agents import Household, Bank, Government, LargeFirm, MediumFirm, SmallFirm
from .utils import get, get_all, avg, split_agents
import itertools
import yaml


def get_bank_money(model):
    return get(model, Bank).money


def get_government_money(model):
    return get(model, Government).money


def get_avg_large_firm_money(model):
    return avg([firm.money for firm in get_all(model, LargeFirm)])

def get_avg_large_firm_goods(model):
    return avg([firm.goods for firm in get_all(model, LargeFirm)])


def get_avg_medium_firm_money(model):
    return avg([firm.money for firm in get_all(model, MediumFirm)])

def get_avg_medium_firm_goods(model):
    return avg([firm.goods for firm in get_all(model, MediumFirm)])


def get_avg_small_firm_money(model):
    return avg([firm.money for firm in get_all(model, SmallFirm)])

def get_avg_small_firm_goods(model):
    return avg([firm.goods for firm in get_all(model, SmallFirm)])


def get_total_household_money(model):
    return sum(household.money for household in get_all(model, Household))


def get_avg_household_money(model):
    return avg({household.money for household in get_all(model, Household)})


def get_household_deposits(model):
    return sum(info["amount"] for info in get(model, Bank).deposits.values())


# load configuration file's variables
with open("src/configuration.yaml", "r") as file:
    data = yaml.safe_load(file)


class MacroModel(mesa.Model):
    household_num = data["NUM_HOUSEHOLDS"]

    # education 2 is the highest, 1 is mid, 0 is bad
    educations = (
        [0] * data["EDUCATION_COUNTS"][0]
        + [1] * data["EDUCATION_COUNTS"][1]
        + [2] * data["EDUCATION_COUNTS"][2]
    )

    def __init__(self, total_steps=data["TOTAL_STEPS"]):
        super().__init__()

        self.total_money = data["HOUSEHOLD_STARTING_MONEY"] * data["NUM_HOUSEHOLDS"] + sum([num_firms * firm_money for (num_firms, firm_money) in zip(data["NUM_FIRMS"].values(), data["FIRM_STARTING_MONEY"].values())])

        self.total_steps = total_steps
        self.schedule = BaseScheduler(self)

        id_giver = itertools.count(1)
        self.schedule.add(Government(next(id_giver), self))
        self.schedule.add(Bank(next(id_giver), self))
        for _ in range(data["NUM_FIRMS"]["LARGE"]):
            self.schedule.add(LargeFirm(next(id_giver), self))

        self.small_firm_ranges = split_agents(data["NUM_FIRMS"]["SMALL"], data["NUM_FIRMS"]["MEDIUM"])

        for i in range(data["NUM_FIRMS"]["MEDIUM"]):
            self.schedule.add(MediumFirm(next(id_giver), self, self.small_firm_ranges[i]))

        self.household_ranges = split_agents(data["NUM_HOUSEHOLDS"], data["NUM_FIRMS"]["SMALL"])
        
        for i in range(data["NUM_FIRMS"]["SMALL"]):
            self.schedule.add(SmallFirm(next(id_giver), self, self.household_ranges[i]))

        for i in range(self.household_num):
            self.schedule.add(Household(next(id_giver), self, self.educations[i]))

        for agent in self.schedule.agents:
            agent.get_references()

        unique_educations = list(set(self.educations))

        data_collectors = {}

        for level in unique_educations:
            data_collectors[f"Education {level + 1} Avg Money"] = (
                lambda model, level=level: avg(
                    [
                        agent.money
                        for agent in model.schedule.agents
                        if isinstance(agent, Household) and agent.education == level
                    ]
                )
            )
            data_collectors[f"Education {level + 1} Avg Goods"] = (
                lambda model, level=level: avg(
                    [
                        agent.goods
                        for agent in model.schedule.agents
                        if isinstance(agent, Household) and agent.education == level
                    ]
                )
            )

        data_collectors.update(
            {
                "Bank Money": get_bank_money,
                "Large Firm Avg Money": get_avg_large_firm_money,
                "Medium Firm Avg Money": get_avg_medium_firm_money,
                "Small Firm Avg Money": get_avg_small_firm_money,
                "Large Firm Avg Goods": get_avg_large_firm_goods,
                "Medium Firm Avg Goods": get_avg_medium_firm_goods,
                "Small Firm Avg Goods": get_avg_small_firm_goods,
                "Government Money": get_government_money,
                "Total Household Money": get_total_household_money,
                "Avg Household Money": get_avg_household_money,
                "Total Household Deposits": get_household_deposits,
            }
        )

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
