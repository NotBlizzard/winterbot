import configparser
import sys
import asyncio
from dotenv import load_dotenv
import os
from bot import Bot

load_dotenv()

if not os.path.exists("permissions.json"):
    print("permissions.json does not exist. making permissions.json.")
    with open("permissions.json", "w") as file:
        file.write("{}")


if not os.path.exists(".env"):
    print(".env does not exist.")
    sys.exit(1)

bot = Bot(
    os.getenv("USERNAME"),
    os.getenv("PASSWORD"),
    os.getenv("ROOMS").split(","),
    os.getenv("KEY"),
    os.getenv("WS"),
    os.getenv("AVATAR"),
)

asyncio.run(bot.connect())
