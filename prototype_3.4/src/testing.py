import yaml

# load configuration file's variables
with open("src/configuration.yaml", "r") as file:
    data = yaml.safe_load(file)

print(data)
print(data["NUM_HOUSEHOLDS"])