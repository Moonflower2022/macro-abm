def get_all(model, agent_class):
    agents = []
    for agent in model.schedule.agents:
        if isinstance(agent, agent_class):
            agents.append(agent)

    if len(agents) > 0:
        return agents
    # elif len(agents) == 0:
    raise Exception(f"uh oh none of agent {agent_class.__name__} found in model")


def get(model, agent_class):
    for agent in model.schedule.agents:
        if isinstance(agent, agent_class):
            return agent
    raise Exception(f"uh oh none of agent {agent_class.__name__} found in model")


def time_due(model, start, interval):
    if model.schedule.time < start:
        return False
    return (model.schedule.time - start) % interval == 0


def avg(arr):
    return sum(arr) / len(arr)


def generate_random_hex_color():
    import random

    return "#" + "".join([random.choice("0123456789abcdef") for _ in range(6)])


def split_households(num_households, num_small_firms):
    num_households_per = num_households / num_small_firms
    return [
        [int(num_households_per * i), int(num_households_per * (i + 1))]
        for i in range(num_small_firms)
    ]


if __name__ == "__main__":
    # Generate a list of 10 random hex colors
    num_colors = 3
    random_hex_colors = [generate_random_hex_color() for _ in range(num_colors)]

    print(random_hex_colors)
