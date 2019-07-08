import configparser
import os
import sys
from winterbot import WinterBot

missing_file = False

if not os.path.exists("permissions.json"):
    missing_file = True
    print("permissions.json does not existing. making permissions.ini.")
    with open("permissions.json", "w") as permissions:
        permissions.write("{}")


if not os.path.exists("config.ini"):
    missing_file = True
    print("config.ini does not exist. making config.ini.")
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
bot = WinterBot(data["username"], data["password"], rooms, data["key"], data["ws"], data["avatar"])
bot.connect()
