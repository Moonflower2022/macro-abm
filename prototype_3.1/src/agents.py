import mesa
from .utils import get, get_all, time_due
import random

# 1 tick is a week


class Bank(mesa.Agent):
    loan_ticks = 8
    

    monthly_interest_rate = 0.005
    compound_interval = 4

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

        self.money = 500

        self.loan_info = []
        self.deposits = {}

    def loan(self, household, amount):
        household.money += amount
        self.money -= amount
        self.loan_info.append({"household": household, "weeks": 0, "amount": amount})

    def demand_loan(self, info):
        if info["amount"] <= self.deposits[info["household"].unique_id]["amount"]:
            self.money += info["amount"]
            self.deposits[info["household"].unique_id]["amount"] -= info["amount"]
        elif info["amount"] <= info["household"].money:
            self.money += info["amount"]
            info["household"].money -= info["amount"]
        else:
            print(
                f"household {info['household'].unique_id} defaulted on loan of {info['amount']}, could only pay back {info['household'].money}"
            )
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
                "start": household.model.schedule.time,
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
        raise Exception(
            "household is trying to withdraw from bank when it doesnt have any deposit money in its name"
        )

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
    rent_interval = 4
    mortgage_interval = 4
    utilities_interval = 4
    goods_interval = 1

    goods_cost = 5
    house_cost = 360
    rent = 15
    utilities_cost = rent / 5
    mortgage_cost = 30
    weekly_goods_consumption = 3
    weekly_goods_consumption_range = 0.25
    monthly_morgage_rate = 0.035

    def __init__(self, unique_id, model, education):
        super().__init__(unique_id, model)
        self.education = education

        self.model = model

        self.money = 20
        self.goods = 0

        self.strategy = "rent"
        self.strategy_start = 0
        self.employed = False
        self.employer = None

    def get_references(self):
        self.bank = get(self.model, Bank)
        self.government = get(self.model, Government)
        self.stores = get_all(self.model, SmallFirm)

    def buy_goods(self):
        lower_bound = (
            self.weekly_goods_consumption - self.weekly_goods_consumption_range
        )
        upper_bound = (
            self.weekly_goods_consumption + self.weekly_goods_consumption_range
        )
        demand = max(random.uniform(lower_bound, upper_bound) - self.goods, 0)

        for store in self.stores:
            if store.goods >= demand:
                store.goods -= demand
                if self.money < demand * self.goods_cost:
                    raise Exception(f"household {self} cant buy food :'(")
                self.money -= demand * self.goods_cost
                break
        print(f"household {self} couldnt find a store to buy food from")

    def pay_rent(self):
        self.money -= self.rent
        self.bank.money += self.rent - self.utilities_cost
        # bank should pay 20% of the rent to the government
        self.government.money += self.utilities_cost

    def pay_utilities(self):
        self.money -= self.utilities_cost
        self.government.money += self.utilities_cost

    def pay_mortgage(self):
        mortgage_after_interest = self.mortgage_cost * (
            1 + self.monthly_morgage_rate
        ) ** ((self.model.schedule.time - self.strategy_start) / 4)
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
            raise Exception(
                "household agent does not have enough money to buy house :("
            )
        self.strategy_start = self.model.schedule.time

    def step(self):
        if self.model.schedule.time == 0:
            self.get_references()

        if self.strategy == "rent" and time_due(
            self.model, self.strategy_start, self.rent_interval
        ):
            self.pay_rent()

        if self.strategy[:8] == "mortgage" and time_due(
            self.model, self.strategy_start, self.mortgage_interval
        ):
            self.pay_mortgage()

        if self.strategy == "own house" and time_due(
            self.model, self.strategy_start, self.utilities_interval
        ):
            self.pay_utilities()

        if self.strategy[:8] == "mortgage":
            if (self.model.schedule.time - self.strategy_start) / 4 >= {
                "A": 3,
                "B": 6,
                "C": 9,
            }[self.strategy[9]]:
                self.strategy = "own house"
                self.strategy_start = self.model.schedule.time

        if time_due(self.model, 0, self.goods_interval):
            self.buy_goods()

        if self.money > 15 and self.strategy == "rent":
            self.bank.deposit(self, self.money - 15)

        elif self.money > 40 and (
            self.strategy[:8] == "mortgage" or self.strategy == "own house"
        ):
            self.bank.deposit(self, self.money - 40)

        if self.money < 15:
            needed_money = 15 - self.money

            if self.bank.money >= needed_money:
                self.bank.loan(self, needed_money)

        if self.model.schedule.time == 14 * 4:  # 14 months
            self.buy_house()


class Government(mesa.Agent):
    money = 500

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)


class Firm(mesa.Agent):
    goods_cost = 5
    minimum_wage = 5

    goods_interval = 1

    def __init__(self, unique_id, model, required_employees, production_quantity):
        super().__init__(unique_id, model)
        self.required_employees = required_employees
        self.production_quantity = production_quantity

        self.employee_counts = [0, 0, 0]
        self.employees = [[], [], []]

        self.money = 250
        self.goods = 0

    def hire_worker(self, education):
        if self.employees[education] == self.required_employees[education]:
            print(
                f"Warning: employees of education level {education} is already at max for firm {self}"
            )
        for worker in get_all(self.model, Household):
            if worker.education == education and worker.employed == False:
                worker.employed = True
                worker.employer = self
                self.employee_counts[education] += 1
                self.employees[education].append(worker)
                break

    def init_workers(self):
        print(self.required_employees)
        for education, count in enumerate(self.required_employees):
            for _ in range(count):
                self.hire_worker(education)

    def fraction_production(self):
        number_required = len(self.required_employees) - self.required_employees.count(
            0
        )
        fraction = sum(
            self.employee_counts[education] / requirement
            for education, requirement in enumerate(self.required_employees)
            if not requirement == 0
        )

        return fraction / number_required

    def worker_fraction_production(self, education):
        if self.employee_counts[education] == 0:
            raise Exception(
                "warning: attempting to find the fraction of product of a worker that does not exist"
            )
        return 1 / (3 * self.required_employees[education])

    def get_references(self):
        pass

    def pay_wages(self, revenue):
        for education_class in self.employees:
            for worker in education_class:
                wage = (
                    revenue * self.worker_fraction_production(worker.education)
                    # + self.minimum_wage
                )
                if self.money < wage:
                    raise Exception(f"Firm defaulted. ID: {self.unique_id}, {self}")
                worker.money += wage
                self.money -= wage

    def acquire_goods(self):
        self.goods += self.production_quantity * self.fraction_production()

    def export_goods(self):
        revenue = 135 * self.fraction_production() * self.goods_cost
        self.money += revenue
        return revenue

    def step(self):
        if self.model.schedule.time == 0:
            self.get_references()
            self.init_workers()

        if time_due(self.model, 0, self.goods_interval):
            self.acquire_goods()
            revenue = self.export_goods()
            self.pay_wages(revenue)


class LargeFirm(Firm):
    def __init__(self, unique_id, model, required_employees, production_quantity):
        super().__init__(unique_id, model, required_employees, production_quantity)

    def get_references(self):
        super().get_references()
        self.firms = get_all(self.model, MediumFirm)

    def step(self):
        super().step()


class MediumFirm(Firm):
    def __init__(self, unique_id, model, required_employees, production_quantity):
        super().__init__(unique_id, model, required_employees, production_quantity)

    def get_references(self):
        super().get_references()
        self.firms = get_all(self.model, SmallFirm)

    def step(self):
        super().step()


class SmallFirm(Firm):
    def __init__(self, unique_id, model, required_employees, production_quantity):
        super().__init__(unique_id, model, required_employees, production_quantity)
