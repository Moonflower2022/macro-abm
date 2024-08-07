import mesa
import random
from .utils import get, get_all, time_due
import yaml

# load configuration file's variables
with open("src/configuration.yaml", "r") as file:
    data = yaml.safe_load(file)

data["TOTAL_GOODS_PRODUCED"] = data["GOODS_PRODUCED"] + data["EXPORT_QUANTITY"]

class Bank(mesa.Agent):
    loan_ticks = data["LOAN_TICKS"]
    monthly_interest_rate = data["MONTHLY_INTEREST_RATE"]
    compound_interval = data["COMPOUND_INTERVAL"]

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

        self.money = data["BANK_STARTING_MONEY"]

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
    rent_interval = data["RENT_INTERVAL"]
    mortgage_interval = data["MORTGAGE_INTERVAL"]
    utilities_interval = data["UTILITIES_INTERVAL"]
    goods_interval = data["GOODS_INTERVAL"]

    house_cost = data["HOUSE_COST"]
    rent = data["RENT"]
    utilities_cost = data["UTILITIES_COST"]
    mortgage_cost = data["MORTGAGE_COST"]
    weekly_goods_consumption = data["WEEKLY_GOODS_CONSUMPTION"]
    weekly_goods_consumption_range = data["WEEKLY_GOODS_CONSUMPTION_RANGE"]
    monthly_mortgage_rate = data["MONTHLY_MORTGAGE_RATE"]

    def __init__(self, unique_id, model, education):
        super().__init__(unique_id, model)
        self.education = education

        self.model = model

        self.money = data["HOUSEHOLD_STARTING_MONEY"]
        self.goods = data["HOUSEHOLD_STARTING_GOODS"]
        self.set_goods_requirement()

        self.strategy = data["HOUSEHOLD_STARTING_STRATEGY"]
        self.strategy_start = 0
        self.employed = False
        self.employer = None

    def get_references(self):
        self.bank = get(self.model, Bank)
        self.government = get(self.model, Government)
        self.stores = get_all(self.model, SmallFirm)

    def set_goods_requirement(self):
        lower_bound = (
            self.weekly_goods_consumption - self.weekly_goods_consumption_range
        )
        upper_bound = (
            self.weekly_goods_consumption + self.weekly_goods_consumption_range
        )

        self.goods_requirement = max(
            random.uniform(lower_bound, upper_bound) - self.goods, 0
        )

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

        if self.money > 15 and self.strategy == "rent":
            self.bank.deposit(self, self.money - 15)

        elif self.money > 40 and (
            self.strategy[:8] == "mortgage" or self.strategy == "own house"
        ):
            self.bank.deposit(self, self.money - 40)

        """
        if self.money < 15:
            needed_money = 15 - self.money

            if self.bank.money >= needed_money:
                self.bank.loan(self, needed_money)
        

        if self.model.schedule.time == 14 * 4:  # 14 months
            self.buy_house()
        """
        self.goods -= self.goods_requirement
        self.set_goods_requirement()


class Government(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

        self.money = data["GOVERNMENT_STARTING_MONEY"]


class Firm(mesa.Agent):
    goods_interval = data["GOODS_INTERVAL"]
    wages_interval = data["WAGES_INTERVAL"]

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.employee_counts = [0, 0, 0]
        self.employees = [[] for _ in range(3)]

    def get_references(self):
        self.households = get_all(self.model, Household)

    def hire_employee(self, education):
        if self.employees[education] == self.required_employees[education]:
            print(
                f"Warning: employees of education level {education} is already at max for firm {self}"
            )
        for worker in self.households:
            if worker.education == education and worker.employed == False:
                worker.employed = True
                worker.employer = self
                self.employee_counts[education] += 1
                self.employees[education].append(worker)
                return

    def init_employees(self):
        for education, count in enumerate(self.required_employees):
            for _ in range(count):
                self.hire_employee(education)

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

    def employee_fraction_production(self, education):
        if self.employee_counts[education] == 0:
            raise Exception(
                "warning: attempting to find the fraction of product of a worker that does not exist"
            )

        return (
            data["SHARE_OF_PRODUCTION_CAPACITY"][education]
            / self.required_employees[education]
        )

    def maximum_capacity_monthly_production_quantity(self):
        return self.goods_requirement * 4

    def pay_wages(self):
        for education_class in self.employees:
            for worker in education_class:
                wage = (
                    self.maximum_capacity_monthly_production_quantity()
                    * data["VALUE_ADDED"]
                    * self.employee_fraction_production(worker.education)
                )
                print("type:", worker)
                print("wage:", wage)
                if self.money < wage:
                    raise Exception(f"Firm defaulted. ID: {self.unique_id}, {self}")
                worker.money += wage
                self.money -= wage

    def sell_goods(self):
        total_quantity = 0

        for customer in self.customers:
            price = (
                self.goods_cost
                * self.fraction_production()
                * customer.goods_requirement
            )

            if customer.money < price:
                raise Exception(f"customer {customer} went bankrupt")
            customer.money -= price
            self.money += price

            if self.goods < customer.goods_requirement:
                raise Exception(f"supplier {self} doesnt have enough goods to provide")

            customer.goods += customer.goods_requirement
            self.goods -= customer.goods_requirement

            total_quantity += customer.goods_requirement

        return total_quantity

    def step(self):
        if self.model.schedule.time == 0:
            self.get_references()
            self.init_employees()

        if time_due(self.model, 0, self.goods_interval):
            self.sell_goods()

        if time_due(self.model, 4, self.wages_interval):
            self.pay_wages()


class LargeFirm(Firm):
    goods_cost = data["VALUE_ADDED"]
    required_employees = data["REQUIRED_EMPLOYEES"]["LARGE"]
    goods_requirement = data["TOTAL_GOODS_PRODUCED"]

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

        self.money = data["FRIM_STARTING_MONEY"]["LARGE"]
        self.goods = data["FRIM_STARTING_GOODS"]["LARGE"]

    def get_references(self):
        super().get_references()
        self.customers = get_all(self.model, MediumFirm)

    def acquire_goods(self):
        self.goods += self.goods_requirement

    def step(self):
        self.acquire_goods()
        super().step()


class MediumFirm(Firm):
    goods_cost = LargeFirm.goods_cost + data["VALUE_ADDED"]
    required_employees = data["REQUIRED_EMPLOYEES"]["MEDIUM"]
    goods_requirement = LargeFirm.goods_requirement / data["NUM_FIRMS"]["MEDIUM"]

    def __init__(self, unique_id, model, customer_range):
        super().__init__(unique_id, model)

        self.money = data["FRIM_STARTING_MONEY"]["MEDIUM"]
        self.goods = data["FRIM_STARTING_GOODS"]["MEDIUM"]
        self.customer_range = customer_range

    def get_references(self):
        super().get_references()
        self.customers = get_all(self.model, SmallFirm)[
            self.customer_range[0] : self.customer_range[1]
        ]

    def step(self):
        super().step()


class SmallFirm(Firm):
    goods_cost = MediumFirm.goods_cost + data["VALUE_ADDED"]
    required_employees = data["REQUIRED_EMPLOYEES"]["SMALL"]
    goods_requirement = LargeFirm.goods_requirement / data["NUM_FIRMS"]["SMALL"]

    def __init__(self, unique_id, model, customer_range):
        super().__init__(unique_id, model)
        self.money = data["FRIM_STARTING_MONEY"]["SMALL"]
        self.goods = data["FRIM_STARTING_GOODS"]["SMALL"]
        self.customer_range = customer_range

    def get_references(self):
        super().get_references()
        self.customers = get_all(self.model, Household)[
            self.customer_range[0] : self.customer_range[1]
        ]

    def sell_extra(self):
        self.money += self.goods * self.goods_cost * self.fraction_production()
        self.goods = 0

    def step(self):
        super().step()
        self.sell_extra()
