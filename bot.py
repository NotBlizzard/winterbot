import websocket
import requests
import json
import time
import re
import os

import commands
import battles
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
        self.ws = websocket.WebSocket()
        self.battles = {}
        self.teams = open("./data/teams.txt", "r").read().lower()

    def __str__(self):
        return f"<CorviknightBot: Main>"

    def login(self, challstr):
        login_data = {"act": "login", "name": self.username, "pass": self.password, "challstr": challstr}
        login = "https://play.pokemonshowdown.com/action.php"
        data = json.loads(requests.post(login, data=login_data).content[1:])
        self.send(f"/trn {self.username},0,{data['assertion']}")
        self.starttime = time.time()  # uptime
        self.timestamp = time.time()
        # prevent old messages from using commands
        self.join(self.rooms)
        self.send(f"/avatar {self.avatar}")

    def parse(self, user, message, battle=False, time_message=False, room=False, pm=False):
        """Parse the message to see if the message has a command."""
        if user == self.username:
            return False

        message = message.split(" ")

        if pm:
            self.command(user, message[0][1:], message[1:], pm=True)
        elif (self.timestamp < int(time_message) and message[0][0] == self.key) or (battle and message[0][0] == self.key):
            self.command(user.strip(), message[0][1:], message[1:])

    def command(self, user, bot_command, args, pm=False):
        """Use getattr to run the command from commands.py"""
        try:
            if hasattr(commands, f"command_{bot_command}"):
                command = getattr(commands, f"command_{bot_command}")
                command_ = command(args, self.room, user, self)

                if command_ is False:
                    return False
                if pm:
                    self.send_pm(user, command_)
                else:
                    self.send(command_, self.room)
        except:
            pass

    def send(self, message, room=""):
        self.ws.send(f"{room}|{message}")

    def send_pm(self, user, message):
        self.ws.send(f"|/pm {user}, {message}")

    def parse_user(self, user):
        user = re.sub(r'[^A-Za-z]', "", user)
        return user

    def battle_accept(self, data):
        data = json.loads(data)
        if data["challengesFrom"] == {}:
            return False
        else:

            user = list(data["challengesFrom"].keys())[0].strip()
            self.send(f"/utm {self.teams}")
            self.send(f"/accept {user}")

    def join(self, rooms):
        for room in rooms:
            self.send(f"/join {room}")

    def hotpatch(self, file):
        reloads = {"commands": commands, "battles": battles}
        try:
            reload(reloads[file])
            return "Hotpatch successful."
        except:
            return "Error."

    def connect(self):
        self.ws.connect(f"ws://{self.ws_url}/showdown/websocket")

        while True:
            messages = self.ws.recv().split("\n")
            for message in messages:

                print(message)
                message = message.split("|")
                message[0] = message[0].strip()

                if len(message) <= 1:
                    message.append("")

                if len(message[0]) > 0 and message[0][0] == ">":
                    self.room = message[0][1:]

                if message[1] == "challstr":
                    self.login("|".join(message[2:]))

                elif message[1] == "c":
                    user = self.parse_user(message[2])
                    self.parse(user, message[3], room=self.room, battle=True)

                elif message[1] == "c:":
                    user = self.parse_user(message[3])
                    self.parse(user, message[4], room=self.room, time_message=message[2])

                elif message[1] == "updatechallenges":
                    self.battle_accept(message[2])

                elif message[1] == "request":
                    if os.path.exists("data/pokedex.json"):
                        # make sure the data exists before accepting the battle
                        if len(message[2]) > 0:
                            if self.room not in list(self.battles.keys()):
                                self.battles[self.room] = battles.Battles(message[2], self.room, self.ws)

                elif message[1] == "pm":
                    user = self.parse_user(message[2])
                    if user != self.username:
                        self.parse(user, message[4], pm=True)

                elif message[1] == "init":
                    if message[2] == "chat":
                        # when the bot joins a new room,
                        # the bot won't spam chat with commands.
                        self.timestamp = time.time()

                if self.room in self.battles.keys():
                    self.battles[self.room].start(message, self.ws)
