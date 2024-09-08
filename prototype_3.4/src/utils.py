def is_whole(num):
    return num == int(num)


def test_is_whole():
    assert is_whole(1) == True
    assert is_whole(1.2) == False
    assert is_whole(1.0) == True

    print('"is_int" funciton testing passed')


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


def split_agents(num_agents, num_managers):

    num_agents_per_manager = num_agents / num_managers
    assert is_whole(num_agents_per_manager)

    return [
        [int(num_agents_per_manager * i), int(num_agents_per_manager * (i + 1))]
        for i in range(num_managers)
    ]


if __name__ == "__main__":
    test_is_whole()

    num_colors = 3
    random_hex_colors = [generate_random_hex_color() for _ in range(num_colors)]

    print(random_hex_colors)
