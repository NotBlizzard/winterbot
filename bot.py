import websockets
import requests
import json
import time
import re
# import asyncio
import commands
from importlib import reload


class Bot:
    def __init__(self, username, password, rooms, key, ws_url, avatar):
        self.username = username
        self.password = password
        self.rooms = rooms
        self.key = key
        self.ws_url = ws_url
        self.avatar = avatar
        self.room = ""
        self.starttime = 0
        self.timestamp = 0

    def __str__(self):
        return f"<{self.username}>"

    async def login(self, challstr):
        login_data = {
            "act": "login",
            "name": self.username,
            "pass": self.password,
            "challstr": challstr
        }
        login_url = "https://play.pokemonshowdown.com/action.php"
        data = requests.post(login_url, data=login_data).content[1:]
        data = json.loads(data)
        await self.send_message(f"/trn {self.username},0,{data['assertion']}")
        self.starttime = time.time()  # uptime
        self.timestamp = time.time()
        # prevent old messages from using commands
        await self.join(self.rooms)
        await self.send_message(f"/avatar {self.avatar}")

    async def parse_message(self, user, message, timestamp):
        """Parse the message to see if the message has a command."""
        if user == self.username:
            return False

        message = message.split()
        bot_command = message[0][1:]
        args = message[1:]
        key = message[0][0]

        if (self.timestamp < int(timestamp)) and key == self.key:
            user = user.strip()
            await self.command(user, bot_command, args)

    async def parse_private_message(self, user, message):
        if user == self.username:
            return False

        message = message.split()
        bot_command = message[0][1:]
        args = message[1:]
        await self.command(user, bot_command, args, pm=True)

    async def command(self, user, bot_command, args, pm=False):
        """Use getattr to run the command from commands.py"""

        if hasattr(commands, f"command_{bot_command}"):
            command_name = getattr(commands, f"command_{bot_command}")
            command = command_name(args, self.room, user, self)

            if command is False:
                return False

            if not pm:
                await self.send_message(command)
            else:
                await self.send_private_message(command, user)

    async def send_message(self, message):
        await self.ws.send(f"{self.room}|{message}")

    async def send_private_message(self, message, user):
        await self.ws.send(f"|/pm {user}, {message}")

    async def join(self, rooms):
        for room in rooms:
            await self.send_message(f"/join {room}")

    def parse_user(self, user):
        return re.sub(r'[^A-Za-z]', "", user)

    def hotpatch(self, file):
        reloads = {"commands": commands}
        reload(reloads[file])
        return "Hotpatch successful."

    async def connect(self):
        ws_url = f"ws://{self.ws_url}/showdown/websocket"
        async with websockets.connect(ws_url) as websocket:
            while True:
                self.ws = websocket
                messages = (await self.ws.recv()).split("\n")
                for message in messages:
                    print(message)
                    message = message.split("|")
                    message[0] = message[0].strip()

                    if len(message) <= 1:
                        message.append("")

                    if len(message[0]) > 0 and message[0][0] == ">":
                        self.room = message[0][1:]

                    if message[1] == "challstr":
                        await self.login("|".join(message[2:]))

                    elif message[1] == "c:":
                        user = self.parse_user(message[3])
                        await self.parse_message(user, message[4], message[2])

                    elif message[1] == "pm":
                        user = self.parse_user(message[2])
                        if user != self.username:
                            await self.parse_private_message(user, message[4])

                    elif message[1] == "init" and message[2] == "chat":
                        self.timestamp = time.time()
