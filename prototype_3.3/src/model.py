import mesa
from mesa.time import BaseScheduler
from mesa.datacollection import DataCollector
from .agents import Household, Bank, Government, LargeFirm, MediumFirm, SmallFirm
from .utils import get, get_all, avg
import itertools


def get_bank_money(model):
    return get(model, Bank).money


def get_government_money(model):
    return get(model, Government).money


def get_avg_large_firm_money(model):
    return avg([firm.money for firm in get_all(model, LargeFirm)])


def get_avg_medium_firm_money(model):
    return avg([firm.money for firm in get_all(model, MediumFirm)])


def get_avg_small_firm_money(model):
    return avg([firm.money for firm in get_all(model, SmallFirm)])


def get_total_household_money(model):
    return sum(household.money for household in get_all(model, Household))


def get_avg_household_money(model):
    return avg({household.money for household in get_all(model, Household)})


def get_household_deposits(model):
    return sum(info["amount"] for info in get(model, Bank).deposits.values())


class MacroModel(mesa.Model):
    household_num = 40

    # education 2 is the highest, 1 is mid, 0 is bad
    educations = [2] * 4 + [1] * 11 + [0] * 25
    # incomes = [40] * 4 + [35] * 11 + [30] * 25

    customer_ranges = [[0, 13], [13, 26], [26, 40]]

    def __init__(self, total_steps=100):
        super().__init__()

        self.total_steps = total_steps
        self.schedule = BaseScheduler(self)

        id_giver = itertools.count(1)
        self.schedule.add(Government(next(id_giver), self))
        self.schedule.add(Bank(next(id_giver), self))
        self.schedule.add(LargeFirm(next(id_giver), self))
        for _ in range(2):
            self.schedule.add(MediumFirm(next(id_giver), self))
        for i in range(3):
            self.schedule.add(SmallFirm(next(id_giver), self, self.customer_ranges[i]))

        household_ids = []
        for i in range(self.household_num):
            household_id = next(id_giver)
            household_ids.append(household_id)
            self.schedule.add(
                Household(household_id, self, self.educations[i])  # self.incomes[i]
            )

        data_collectors = {}

        unique_educations = list(set(self.educations))

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
                "Large Firm Money": get_avg_large_firm_money,
                "Medium Firm Money": get_avg_medium_firm_money,
                "Small Firm Money": get_avg_small_firm_money,
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
