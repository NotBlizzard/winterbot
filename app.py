import configparser
import os
import sys
from bot import Bot

missing_file = False


for x in ["permissions.json", "./data/teams.txt"]:
    if not os.path.exists(x):
        print(f"\"${x}\" does not exist. making \"{x}\"")
        with open(x, "w") as file:
            file.write("{}")


if not os.path.exists("config.ini"):
    missing_file = True
    print("\"config.ini\" does not exist. making \"config.ini\"")
    config = configparser.ConfigParser()
    config["POKEMON"] = {
        "username": "",
        "password": "",
        "rooms": "",
        "ws": "",
        "key": "",
        "avatar": "",
        "moves": "",
        "pokedex": "",
        "typechart": ""
    }

    with open("config.ini", "w") as config_:
        config.write(config_)


if missing_file:
    sys.exit(1)

data = configparser.ConfigParser()
data.read("config.ini")
data = data["POKEMON"]
rooms = [x for x in data["rooms"].split(",") if len(x) > 1]
bot = Bot(data["username"], data["password"], rooms, data["key"], data["ws"], data["avatar"])
bot.connect()
