import mesa
from mesa.visualization.modules import ChartModule
from .model import MacroModel

COLORS = ["#2596be", "#e28743", "#21130d"]

chart = ChartModule(
    [
        {"Label": "Bank Money", "Color": "#2ca02c"},
        {"Label": "Large Firm Money", "Color": "#12fe1e"},
        {"Label": "Medium Firm Money", "Color": "#f14b5a"},
        {"Label": "Large Firm Money", "Color": "#000000"},
        {"Label": "Government Money", "Color": "#1f77b4"},
        {"Label": "Total Household Money", "Color": "#ff7f0e"},
        {"Label": "Total Household Deposits", "Color": "000000"}
    ]
)

chart2 = ChartModule(
    [
        {"Label": "Education 1 Avg Money", "Color": COLORS[0]},
        {"Label": "Education 2 Avg Money", "Color": COLORS[1]},
        {"Label": "Education 3 Avg Money", "Color": COLORS[2]},
        {"Label": "Education 1 Avg Goods", "Color": COLORS[0]},
        {"Label": "Education 2 Avg Goods", "Color": COLORS[1]},
        {"Label": "Education 3 Avg Goods", "Color": COLORS[2]},
    ]
)

total_steps = 100

server = mesa.visualization.ModularServer(
    MacroModel, [chart, chart2], "Macro Model", {"total_steps": total_steps}
)
server.port = 8520
