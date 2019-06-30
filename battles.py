import json
from logic import Logic


class Battles:
    # Battles of Pokemon Showdown.
    def __init__(self, data, room, ws):
        self.data = json.loads(data)
        self.team = self.data["side"]["pokemon"]
        self.room = room
        self.active_room = None
        self.format = self.room.split("-")[1]
        self.ws = ws
        self.id = self.data["side"]["id"]
        self.active_pokemon = None
        self.opponent_pokemon = None
        self.organize_team()
        self.battlelogic = Logic(self.team, self.id, self.room)
        self.ws.send("{}|GLHF.".format(self.room))

    def __str__(self):
        return "<WinterBot Battle {}>".format(self.room)

    def organize_team(self):
        team = {}
        for pokemon in self.team:
            name = pokemon["ident"].split(" ")[1:][0].lower()
            team[name] = {}
            team[name]["active"] = pokemon["active"]
            team[name]["moves"] = pokemon["moves"]
            team[name]["ability"] = pokemon["ability"]
            team[name]["item"] = pokemon["item"]
            team[name]["fainted"] = False

        self.team = team

    def get_active_and_opponent_pokemon(self, message):

        if self.id == message[2][0:2]:
            self.active_pokemon = message[2].lower()[5:].strip()
            self.battlelogic.best_choice_band_move = ""
        else:
            self.opponent_pokemon = message[2].lower()[5:].strip()

    def start(self, message, ws):

        if len(message) <= 1:
            message.append("")

        if len(message[0]) > 0 and message[0][0] == ">":
            self.active_room = message[0][1:]

        if self.active_room == self.room:

            if message[1] == "teampreview":
                self.active_pokemon = list(self.team.keys())[0]
                self.ws.send("{}|/team 1".format(self.active_room))

            if message[1] == "switch":
                self.get_active_and_opponent_pokemon(message)

            if message[1] in ["request", "turn"]:
                self.battlelogic.logic(self.active_pokemon, self.opponent_pokemon, self.ws, "move")

            if message[1] == "faint":
                if self.id == message[2][0:2]:
                    self.battlelogic.logic(self.active_pokemon, self.opponent_pokemon, self.ws, "swap")

            if message[1] == "error":
                if "switch response" in message[2]:
                    self.battlelogic.logic(self.active_pokemon, self.opponent_pokemon, self.ws, "swap")

                if "is disabled" in message[2]:
                    # stuff like hydro pump
                    self.battlelogic.logic(self.active_pokemon, self.opponent_pokemon, self.ws, "new move")

            if message[1] == "-status":
                if self.id != message[2][0:2] and len(message) > 3:
                    # maybe the opponent has psn/brn on them
                    self.battlelogic.logic(self.active_pokemon, self.opponent_pokemon, self.ws, message[3])

            if message[1] == "detailschange":
                # mega evolution
                if self.id != message[2][0:2]:
                    self.battlelogic.logic(self.active_pokemon, self.opponent_pokemon, self.ws, "mega")

            if message[1] == "drag":
                if self.id == message[2][0:2]:
                    self.active_pokemon = message[2][5:].lower()

            if message[1] in ["win", "loss"]:
                self.ws.send("{}|good game.".format(self.active_room))
                self.ws.send("{}|/leave".format(self.active_room))
