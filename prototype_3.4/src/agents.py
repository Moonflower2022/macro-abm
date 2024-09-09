import mesa
import random
from .utils import get, get_all, time_due
import yaml

# load configuration file's variables
with open("src/configuration.yaml", "r") as file:
    data = yaml.safe_load(file)

data["TOTAL_GOODS_PRODUCED"] = data["GOODS_PRODUCED"] + data["TOTAL_EXPORT_QUANTITY"]


class BaseAgent(mesa.Agent):
    def get_references(self):
        pass


class Bank(BaseAgent):
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


class Household(BaseAgent):
    rent_interval = data["RENT_INTERVAL"]
    mortgage_interval = data["MORTGAGE_INTERVAL"]
    utilities_interval = data["UTILITIES_INTERVAL"]
    goods_interval = data["GOODS_INTERVAL"]

    house_cost = data["HOUSE_COST"]
    rent_cost = data["RENT_COST"]
    utilities_cost = data["UTILITIES_COST"]
    mortgage_cost = data["MORTGAGE_COST"]
    weekly_goods_consumption = data["WEEKLY_GOODS_CONSUMPTION"]
    weekly_goods_consumption_range = data["WEEKLY_GOODS_CONSUMPTION_RANGE"]
    monthly_mortgage_rate = data["MONTHLY_MORTGAGE_RATE"]
    weekly_temporal_discount_rate = data["WEEKLY_TEMPORAL_DISCOUNT_RATE"]

    def __init__(self, unique_id, model, education):
        super().__init__(unique_id, model)
        self.education = education

        self.model = model

        self.money = data["HOUSEHOLD_STARTING_MONEY"]
        self.goods = data["HOUSEHOLD_STARTING_GOODS"]

        self.strategy = data["HOUSEHOLD_STARTING_STRATEGY"]
        self.strategy_start = 0
        self.employed = False
        self.employer = None

    def get_references(self):
        self.bank = get(self.model, Bank)
        self.government = get(self.model, Government)
        self.stores = get_all(self.model, SmallFirm)
        self.after_references()

    def after_references(self):
        self.set_goods_requirement()
        self.buy_imported_goods()


    def set_goods_requirement(self):
        lower_bound = (
            self.weekly_goods_consumption - self.weekly_goods_consumption_range
        )
        upper_bound = (
            self.weekly_goods_consumption + self.weekly_goods_consumption_range
        )

        self.goods_requirement = random.uniform(lower_bound, upper_bound)

    def buy_imported_goods(self):
        quantity = data["TOTAL_IMPORT_QUANTITY"] / data["NUM_HOUSEHOLDS"]

        self.goods_requirement -= quantity
        amount = data["IMPORT_PRICE"] * quantity * self.government.compounded_inflation_rate
        self.money -= amount
        self.model.total_money -= amount

    def get_goods_requirement(self):
        return max(self.goods_requirement - self.goods, 0)

    def pay_rent(self):
        self.money -= self.rent_cost
        self.bank.money += self.rent_cost - self.utilities_cost
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
        if self.goods < self.goods_requirement:
            raise Exception(
                f"household {self} does not have enough food to consume"
            )
        self.goods -= self.goods_requirement
        self.set_goods_requirement()
        self.buy_imported_goods()


class Government(BaseAgent):
    inflation_interval = data["INFLATION_INTERVAL"]

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

        self.money = data["GOVERNMENT_STARTING_MONEY"]
        self.total_money_provided = 0

        self.compounded_inflation_rate = 1

    def get_references(self):
        self.initial_total_money = self.model.total_money

    def provide_money(self, household, price, weekly_temporal_discount_rate, quantity):
        amount = price * (1 - weekly_temporal_discount_rate) * quantity
        household.money += amount
        self.model.total_money += amount
        self.total_money_provided += amount

    def get_inflation_factor(self):
        return 1 + (self.total_money_provided / self.initial_total_money)

    def step(self):
        if time_due(self.model, 0, self.inflation_interval):
            self.compounded_inflation_rate *= self.get_inflation_factor()
            print("\ninflation rate:", self.compounded_inflation_rate, "\n")


class Firm(BaseAgent):
    goods_interval = data["GOODS_INTERVAL"]
    wages_interval = data["WAGES_INTERVAL"]

    @property
    def goods_cost(self):
        return self.base_goods_cost * self.government.compounded_inflation_rate

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.employee_counts = [0, 0, 0]
        self.employees = [[] for _ in range(3)]

        self.monthly_inflation_rate_sum = 0

    def get_references(self):
        self.households = get_all(self.model, Household)
        self.government = get(self.model, Government)

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

    def pay_wages(self):
        print(
            "firm:",
            self,
            "month_good_quantity:",
            self.month_goods_quantity,
            "monthly_inflation_rate_sum:",
            self.monthly_inflation_rate_sum,
            "money:",
            self.money,
        )
    
        total_wages = 0

        for education_class in self.employees:
            for worker in education_class:
                wage = (
                    self.month_goods_quantity
                    * data["VALUE_ADDED"]
                    * self.employee_fraction_production(worker.education)
                    * (self.monthly_inflation_rate_sum / 4)
                )
                if self.money < wage:
                    raise Exception(f"Firm {self} defaulted. ID: {self.unique_id}")
                worker.money += wage
                self.money -= wage

                total_wages += wage

        print(f"new money: {self.money}")

    def get_goods_requirement(self):
        return max(
            sum([customer.get_goods_requirement() for customer in self.customers])
            - self.goods
            + (self.export_quantity if isinstance(self, SmallFirm) else 0)
            + 1e-8,  # for rounding problem preventation
            0,
        )

    def sell_goods(self):
        total_quantity = 0

        for customer in self.customers:
            quantity = customer.get_goods_requirement()

            if isinstance(self, SmallFirm):
                self.government.provide_money(
                    customer,
                    self.goods_cost,
                    customer.weekly_temporal_discount_rate,
                    quantity,
                )

            price = (
                self.goods_cost
                * self.fraction_production()
                * quantity
                * self.government.compounded_inflation_rate
            )

            if customer.money < price:
                raise Exception(f"customer {customer} went bankrupt")
            customer.money -= price
            self.money += price

            if self.goods < quantity:
                raise Exception(f"supplier {self} doesnt have enough goods to provide")

            customer.goods += quantity
            self.goods -= quantity

            total_quantity += quantity

        return total_quantity

    def step(self):
        if isinstance(self, LargeFirm):
            self.acquire_goods()

        if self.model.schedule.time == 0:
            self.init_employees()

        if time_due(self.model, 0, self.goods_interval):
            self.month_goods_quantity += self.sell_goods() + (
                0 if not isinstance(self, SmallFirm) else self.export()
            )
            self.monthly_inflation_rate_sum += self.government.compounded_inflation_rate

        if time_due(self.model, 3, self.wages_interval):
            self.pay_wages()
            self.month_goods_quantity = 0
            self.monthly_inflation_rate_sum = 0


class LargeFirm(Firm):
    base_goods_cost = data["VALUE_ADDED"]

    required_employees = data["REQUIRED_EMPLOYEES"]["LARGE"]
    goods_requirement = data["TOTAL_GOODS_PRODUCED"]
    export_quantity = data["TOTAL_EXPORT_QUANTITY"]

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

        self.money = data["FIRM_STARTING_MONEY"]["LARGE"]
        self.goods = data["FIRM_STARTING_GOODS"]["LARGE"]

        self.month_goods_quantity = 0

    def get_references(self):
        super().get_references()
        self.customers = get_all(self.model, MediumFirm)

    def acquire_goods(self):
        self.goods += self.get_goods_requirement()


class MediumFirm(Firm):
    base_goods_cost = LargeFirm.base_goods_cost + data["VALUE_ADDED"]

    required_employees = data["REQUIRED_EMPLOYEES"]["MEDIUM"]
    goods_requirement = LargeFirm.goods_requirement / data["NUM_FIRMS"]["MEDIUM"]
    export_quantity = data["TOTAL_EXPORT_QUANTITY"] / data["NUM_FIRMS"]["MEDIUM"]

    def __init__(self, unique_id, model, customer_range):
        super().__init__(unique_id, model)

        self.money = data["FIRM_STARTING_MONEY"]["MEDIUM"]
        self.goods = data["FIRM_STARTING_GOODS"]["MEDIUM"]
        self.customer_range = customer_range

        self.month_goods_quantity = 0

    def get_references(self):
        super().get_references()
        self.customers = get_all(self.model, SmallFirm)[
            self.customer_range[0] : self.customer_range[1]
        ]


class SmallFirm(Firm):
    base_goods_cost = MediumFirm.base_goods_cost + data["VALUE_ADDED"]

    required_employees = data["REQUIRED_EMPLOYEES"]["SMALL"]
    goods_requirement = LargeFirm.goods_requirement / data["NUM_FIRMS"]["SMALL"]
    export_quantity = data["TOTAL_EXPORT_QUANTITY"] / data["NUM_FIRMS"]["SMALL"]

    def __init__(self, unique_id, model, customer_range):
        super().__init__(unique_id, model)
        self.money = data["FIRM_STARTING_MONEY"]["SMALL"]
        self.goods = data["FIRM_STARTING_GOODS"]["SMALL"]
        self.customer_range = customer_range

        self.month_goods_quantity = 0

    # def get_goods_requirement(self):
    #    return max(self.goods_requirement - self.goods, 0)

    def get_references(self):
        super().get_references()
        self.customers = get_all(self.model, Household)[
            self.customer_range[0] : self.customer_range[1]
        ]
        self.government = get(self.model, Government)

    def export(self):
        if self.goods < self.export_quantity:
            print("small firm goods:", self.goods)
            raise Exception(f"small firm {self} doesn't have enough goods to export")

        amount = self.export_quantity * data["EXPORT_PRICE"] * self.government.compounded_inflation_rate
        self.money += amount
        self.model.total_money += amount
        self.goods -= self.export_quantity
        return self.export_quantity
