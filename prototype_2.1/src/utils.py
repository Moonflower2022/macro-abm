def get_all(model, agent_class):
    agents = []
    for agent in model.schedule.agents:
        if isinstance(agent, agent_class):
            agents.append(agent)

    if len(agents) > 0:
        return agents
    # len(agents) == 0
    raise Exception(f"uh oh none of agent {agent_class.__name__} found in model")


def get(model, agent_class):
    for agent in model.schedule.agents:
        if isinstance(agent, agent_class):
            return agent
    raise Exception(f"uh oh none of agent {agent_class.__name__} found in model")

def time_due(model, start, interval):
    return (model.schedule.time - start) % interval == 0