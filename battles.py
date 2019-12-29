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
        self.logic = Logic(self.team, self.id, self.room, self.ws)
        self.ws.send(f"{self.room}|GLHF.")

    def __str__(self):
        return f"<CorviknightBot: Battle {self.room}>"

    def organize_team(self):
        team = {}
        for pokemon in self.team:
            name = pokemon["ident"].split(" ")[1:][0].lower().replace(" ", "")
            team[name] = {}
            team[name]["active"] = pokemon["active"]
            team[name]["moves"] = pokemon["moves"]
            team[name]["ability"] = pokemon["ability"]
            team[name]["item"] = pokemon["item"]
            team[name]["fainted"] = False

        self.team = team

    def get_active_and_opponent_pokemon(self, message):

        if self.id == message[2][0:2]:
            self.active_pokemon = message[2].lower()[5:].strip().replace(' ', '')
            self.logic.best_choice_band_move = ""
        else:
            self.opponent_pokemon = message[2].lower()[5:].strip()

    def start(self, message, ws):

        if len(message) <= 1:
            message.append("")

        if len(message[0]) > 0 and message[0][0] == ">":
            self.active_room = message[0][1:]

        if message[1] == "teampreview":
            self.active_pokemon = list(self.team.keys())[0]
            self.ws.send(f"{self.room}|/team 1")

        elif message[1] == "switch":
            self.get_active_and_opponent_pokemon(message)

        elif message[1] in ["request", "turn", "player"]:
            self.logic.start(self.active_pokemon, self.opponent_pokemon)

        elif message[1] == "player":
            self.logic.start(self.active_pokemon, self.opponent_pokemon)

        elif message[1] == "faint":
            if self.id == message[2][0:2]:
                self.logic.start(self.active_pokemon, self.opponent_pokemon, "swap")

        elif message[1] == "error":
            if "switch response" in message[2]:
                self.logic.start(self.active_pokemon, self.opponent_pokemon, "swap")

            if "is disabled" in message[2]:
                # stuff like hydro pump
                self.logic.start(self.active_pokemon, self.opponent_pokemon, "new move")

        elif message[1] == "-status":
            if self.id != message[2][0:2] and len(message) > 3:
                # maybe the opponent has psn/brn on them
                self.logic.start(self.active_pokemon, self.opponent_pokemon, message[3])

        elif message[1] == "drag":
            if self.id == message[2][0:2]:
                self.active_pokemon = message[2][5:].lower().replace(" ", "")

        elif message[1] in ["win", "loss"]:
            self.ws.send(f"{self.room}|good game.")
            self.ws.send(f"{self.room}|/leave")
