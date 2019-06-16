import websocket
import requests
import json
import time
import re

import commands
import battles
from importlib import reload


class WinterBot:

    def __init__(self, username, password, rooms, key, ws_url, avatar):
        self.username = username
        self.password = password
        self.rooms = rooms
        self.key = key
        self.ws_url = ws_url
        self.avatar = avatar
        self.room = ""
        self.timestamp = 0
        self.ws = websocket.WebSocket()
        self.login_url = "https://play.pokemonshowdown.com/action.php"
        self.battles = {}
        self.team = open("./data/teams.txt", "r").read().strip()

    def __str__(self):
        return "<WinterBot Main>"

    def login(self, challstr):
        """Log into PokemonShowdown"""
        login_data = {"act": "login", "name": self.username, "pass": self.password, "challstr": challstr}
        data = json.loads(requests.post(self.login_url, data=login_data).content[1:])
        self.ws.send("|/trn {},0,{}".format(self.username, data["assertion"]))
        self.timestamp = time.time()
        # prevent old messages from using commands
        self.join(self.rooms)
        self.ws.send("|/avatar {}".format(self.avatar))

    def parse_message(self, time_message, user, message, current_room, battle):
        """Parsing the message. If it's a command, the data
           is sent to command()"""
        if (self.timestamp < int(time_message) and message[0] == self.key) or battle and message[0] == self.key:
            message = message.split(" ")
            self.command(time_message, user.strip(), message[0][1:], message[1:], current_room)

    def command(self, time_message, user, bot_command, args, current_room):
        """Using getattr to use the command"""

        if bot_command == "hotpatch":
            self.hotpatch(user, args)

        # eval
        if bot_command == "eval":
            getattr(commands, "command_{}".format(bot_command), __name__)(args, user, current_room, self.ws, self)
        else:
            try:
                getattr(commands, "command_{}".format(bot_command), __name__)(args, user, current_room, self.ws)
            except:
                pass

    def battle_accept(self, data):
        """Accept battles sent"""
        data = json.loads(data)
        if data["challengesFrom"] == {}:
            return False
        else:

            user = list(data["challengesFrom"].keys())[0].strip()
            self.ws.send("|/utm {}".format(self.team))
            self.ws.send("|/accept {}".format(user))

    def join(self, rooms):
        """Join rooms"""

        for room in rooms:
            self.ws.send("|/join {}".format(room))

    def hotpatch(self, user, args):
        if commands.permission(user, 4):
            reloads = {"commands": commands, "battles": battles}
            try:
                if args[0] in list(reloads.keys()):
                    reload(reloads[args[0]])
                    self.ws.send("{}|Reload of {} successful.".format(self.room, args[0]))
            except:
                pass

    def connect(self):
        """Connect to the websocket"""
        self.ws.connect(self.ws_url)

        while True:
            messages = [message for message in self.ws.recv().split("\n")]
            for message in messages:
                print(message)
                message = message.split("|")
                if len(message) <= 1:
                    message.append("")

                if len(message[0]) > 0 and message[0][0] == ">":
                    self.room = message[0][1:]

                if message[1] == "challstr":
                    self.login("|".join(message[2:]))

                if message[1] == "c":
                    self.parse_message(1, re.sub(r'[^A-Za-z]', "", message[2]), message[3], self.room, True)

                if message[1] == "c:":
                    self.parse_message(message[2], message[3], message[4], self.room, False)

                if message[1] == "updatechallenges":
                    self.battle_accept(message[2])

                if message[1] == "request":
                    if len(message[2]) > 0:
                        if self.room not in list(self.battles.keys()):
                            self.battles[self.room] = battles.Battles(message[2], self.room, self.ws)

                if self.room in self.battles.keys():
                    self.battles[self.room].start(message, self.ws)
