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
        self.battles = {}

    def __str__(self):
        return "<WinterBot Main>"

    def login(self, challstr):
        login_data = {"act": "login", "name": self.username, "pass": self.password, "challstr": challstr}
        login = "https://play.pokemonshowdown.com/action.php"
        data = json.loads(requests.post(login, data=login_data).content[1:])
        self.send("/trn {},0,{}".format(self.username, data["assertion"]))
        self.timestamp = time.time()
        # prevent old messages from using commands
        self.join(self.rooms)
        self.send("/avatar {}".format(self.avatar))

    def parse(self, user, message, battle=False, time_message=False, room=False, pm=False):
        """Parse the message to see if the message has a command."""

        message = message.split(" ")

        if pm:
            self.command(user, message[0][1:], message[1:], pm=True)
        elif (self.timestamp < int(time_message) and message[0][0] == self.key) or (battle and message[0][0] == self.key):
            self.command(user.strip(), message[0][1:], message[1:])

    def command(self, user, bot_command, args, pm=False):
        """Use getattr to run the command from commands.py"""
        try:
            command = getattr(commands, "command_{}".format(bot_command))
            command_ = command(args, self.room, user, self)
            if pm:
                self.send_pm(user, command_)
            else:
                self.send(command_, self.room)
        except:
            raise

    def send(self, message, room=""):
        self.ws.send("{}|{}".format(room, message))

    def send_pm(self, user, message):
        self.ws.send("|/pm {}, {}".format(user, message))

    def parse_user(self, user):
        user = re.sub(r'[^A-Za-z]', "", user)
        return user

    def battle_accept(self, data):
        data = json.loads(data)
        if data["challengesFrom"] == {}:
            return False
        else:

            user = list(data["challengesFrom"].keys())[0].strip()
            self.send("/utm")
            self.send("/accept {}".format(user))

    def join(self, rooms):
        for room in rooms:
            self.send("/join {}".format(room))


    def hotpatch(self, file):
        reloads = {"commands": commands, "battles": battles}
        try:
            reload(reloads[file])
            return "Hotpatch successful."
        except:
            return "Error."

    def connect(self):
        self.ws.connect(self.ws_url)

        while True:
            messages = [message for message in self.ws.recv().split("\n")]
            for message in messages:

                print(message)

                if len(message) == 0:
                    self.room = ""

                message = message.split("|")

                if len(message) <= 1:
                    message.append("")

                if len(message[0]) > 0 and message[0][0] == ">":
                    self.room = message[0][1:]

                if message[1] == "challstr":
                    self.login("|".join(message[2:]))

                if message[1] == "c":
                    user = self.parse_user(message[2])
                    self.parse(user, message[3], room=self.room)

                if message[1] == "c:":
                    user = self.parse_user(message[3])
                    self.parse(user, message[4], room=self.room, time_message=message[2])

                if message[1] == "updatechallenges":
                    self.battle_accept(message[2])

                if message[1] == "request":
                    if len(message[2]) > 0:
                        if self.room not in list(self.battles.keys()):
                            self.battles[self.room] = battles.Battles(message[2], self.room, self.ws)

                if message[1] == "pm":
                    user = self.parse_user(message[2])
                    if user != self.username:
                        self.parse(user, message[4], pm=True)

                if message[1] == "init":
                    if message[2] == "chat":
                        # when the bot joins a new room,
                        # the bot won't spam chat with commands.
                        self.timestamp = time.time()

                if self.room in self.battles.keys():
                    self.battles[self.room].start(message, self.ws)
