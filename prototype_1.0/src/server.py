import mesa
from .model import MacroModel

LOANS_COLOR = "#2ca02c"
TOTAL_CASH_COLOR = "#d62728"
TOTAL_DEPOSITS_COLOR = "#3a2b81"
CASH_COLORS = [
    "#2596be",
    "#e28743",
    "#21130d"
]


chart = mesa.visualization.ChartModule(
    [
        {"Label": "Bank Money", "Color": LOANS_COLOR},
        {"Label": "Total Cash", "Color": TOTAL_CASH_COLOR},
        {"Label": "Total Deposits", "Color": TOTAL_DEPOSITS_COLOR}
    ]
)

chart2 = mesa.visualization.ChartModule(
    [
        {"Label": "Cash 1", "Color": CASH_COLORS[0]},
        {"Label": "Cash 2", "Color": CASH_COLORS[1]},
        {"Label": "Cash 3", "Color": CASH_COLORS[2]},
    ]
)

total_steps = 100

server = mesa.visualization.ModularServer(MacroModel, [chart, chart2], "Macro Model", {"total_steps": total_steps})
server.port = 8520