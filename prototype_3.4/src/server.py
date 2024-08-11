import mesa
from mesa.visualization.modules import ChartModule
from .model import MacroModel

HOUSEHOLD_COLORS = ["#2596be", "#e28743", "#21130d"]
FIRM_COLORS = ["#12fe1e", "#f14b5a", "#000000"]

chart = ChartModule(
    [
        #{"Label": "Bank Money", "Color": "#2ca02c"},
        {"Label": "Large Firm Avg Money", "Color": FIRM_COLORS[2]},
        {"Label": "Medium Firm Avg Money", "Color": FIRM_COLORS[1]},
        {"Label": "Small Firm Avg Money", "Color": FIRM_COLORS[0]},
    ]
)

chart2 = ChartModule(
    [
        {"Label": "Education 1 Avg Money", "Color": HOUSEHOLD_COLORS[0]},
        {"Label": "Education 2 Avg Money", "Color": HOUSEHOLD_COLORS[1]},
        {"Label": "Education 3 Avg Money", "Color": HOUSEHOLD_COLORS[2]},
        #{"Label": "Education 1 Avg Goods", "Color": COLORS[0]},
        #{"Label": "Education 2 Avg Goods", "Color": COLORS[1]},
        #{"Label": "Education 3 Avg Goods", "Color": COLORS[2]},
    ]
)

chart3 = ChartModule(
    [
        {"Label": "Large Firm Avg Goods", "Color": FIRM_COLORS[2]},
        {"Label": "Medium Firm Avg Goods", "Color": FIRM_COLORS[1]},
        {"Label": "Small Firm Avg Goods", "Color": FIRM_COLORS[0]}
    ]
)

total_steps = 100

server = mesa.visualization.ModularServer(
    MacroModel, [chart, chart2, chart3], "Macro Model", {"total_steps": total_steps}
)
server.port = 8520
