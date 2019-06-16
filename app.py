import configparser
from winterbot import WinterBot

data = configparser.ConfigParser()
data.read("config.ini")
data = data["POKEMON"]
rooms = [x for x in data["ROOMS"].split(",") if len(x) > 1]
bot = WinterBot(data["USERNAME"], data["PASSWORD"], rooms, data["KEY"], data["WS"], data["AVATAR"])
bot.connect()
