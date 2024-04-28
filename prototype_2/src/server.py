import mesa
from mesa.visualization.modules import ChartModule
from .model import MacroModel

CASH_COLORS = ["#2596be", "#e28743", "#21130d"]

chart = ChartModule(
    [
        {"Label": "Bank Money", "Color": "#2ca02c"},
        {"Label": "Firm Money", "Color": "#f14b5a"},
        {"Label": "Government Money", "Color": "#d62728"},
        {"Label": "Total Household Money", "Color": "#d62728"},
    ]
)

chart2 = ChartModule(
    [
        {"Label": "Household 1 Money", "Color": CASH_COLORS[0]},
        {"Label": "Household 2 Money", "Color": CASH_COLORS[1]},
        {"Label": "Household 3 Money", "Color": CASH_COLORS[2]},
    ]
)

total_steps = 100

server = mesa.visualization.ModularServer(
    MacroModel, [chart, chart2], "Macro Model", {"total_steps": total_steps}
)
server.port = 8520