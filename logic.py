import json
from collections import Counter
from re import sub
import random
from functools import reduce
import configparser

data = configparser.ConfigParser()
data.read("config.ini")
files = data["POKEMON"]


class Logic:
    """Logic of the Pokemon battles.
       etc. switching, attacking.
    """
    def __init__(self, team, _id, room, ws):
        self.team = team
        self.id = _id
        self.room = room
        self.ws = ws
        self.moves = json.loads(open(files["moves"], "r").read().lower())
        self.pokedex = json.loads(open(files["pokedex"], "r").read().lower())
        self.typechart = json.loads(open(files["typechart"], "r").read().lower())
        self.active_pokemon_moves = None
        self.status_move_usable = False  # toxic, thunderwave, etc.
        self.opponent_pokemon_status = {}
        self.active_pokemon = None
        self.opponent_pokemon = None
        self.best = ""
        # choice items: choice band, choice scarf, choice specs.
        self.choice_band = ""

    def __str__(self):
        return f"<WinterBot: Logic {self.room}>"

    def organize_moves(self):

        self.team[self.active_pokemon]["moves"] = [sub(r'[^A-Za-z]', '', x).lower() for x in self.team[self.active_pokemon]["moves"]]
        moves = [{"name": x, "type": self.moves[x]["type"], "dmg": self.moves[x]["basepower"]} for x in self.team[self.active_pokemon]["moves"]]

        for x in moves:
            if "status" in list(self.moves[x["name"]].keys()):
                self.status_move_usable = True
                x["status"] = True
                x["statuseffect"] = self.moves[x["name"]]["status"]
            else:
                self.status_move_usable = False

        return moves

    def get_effectiveness(self, weaknesses_):
        weaknesses__ = {}
        for a in weaknesses_:
            # going through weaknesses_, seeing how many times
            # "super", "resistant", "immune", "normal" show up.
            # ex: "super" shows up twice,
            # so the ability is 4x effective against the pokemon
            data = {"super": "2.0", "resistant": "0.50", "immune": "0.0", "normal": "1.0"}
            weaknesses__[a] = [data[x] for x in weaknesses_[a]]

        weaknesses__ = {z: reduce(lambda x, y: float(x) * float(y), weaknesses__[z]) for z in weaknesses__}
        return weaknesses__

    def get_opponent_pokemon_type(self):
        return [x.lower() for x in self.pokedex[self.opponent_pokemon]["types"]]

    def get_type_effectiveness(self, opponent_pokemon_type):
        weaknesses = {}
        for move in self.active_pokemon_moves:
            # going through each pokemon move the active pokemon has
            move_type = move["type"]
            for a in opponent_pokemon_type:
                # going through each pokemon type the opponent has
                # getting weaknesses for each people type the opponent has
                weakness = self.typechart[a]["damagetaken"]
                # making sure key doesn't already exist
                if move["name"] not in weaknesses.keys():
                    weaknesses[move["name"]] = {}
                # make a dict, puts the ability,
                # and then how effective it is against said type
                # ex: thunderbolt is super effective against flying,
                # but not effective aginst electric

                weaknesses[move["name"]][a] = weakness[move_type]

        return weaknesses

    def get_opponent_pokemon_status(self):
        # get status effect of opponent pokemon
        if self.opponent_pokemon not in self.opponent_pokemon_status:
            if self.status_move_usable:
                self.best = [x for x in self.active_pokemon_moves if "status" in x.keys()][0]["name"]
                return True
        else:
            return False

    def swap(self):
        self.team[self.active_pokemon]["fainted"] = True

        self.choice_band = ""
        for pokemon in self.team:
            if not self.team[pokemon]["fainted"]:
                # swap to the first non-fainted pokemon in team
                self.team[pokemon]["active"] = True
                return self.ws.send(f"{self.room}|/switch {pokemon}")

    def new_move(self):
        new_move = random.choice(self.team[self.active_pokemon]["moves"])
        return self.ws.send(f"{self.room}|/move {new_move}")

    def start(self, active_pokemon, opponent_pokemon, action=None):
        self.active_pokemon = active_pokemon
        self.opponent_pokemon = opponent_pokemon

        if self.opponent_pokemon is None:
            return True

        if action == "swap":
            return self.swap()

        elif action == "new move":
            return self.new_move()

        elif action in ["tox", "brn", "slp", "par"]:
            self.opponent_pokemon_status[self.opponent_pokemon] = action

        if self.choice_band != "":
            return self.ws.send(f"{self.room}|/move {self.choice_band}")

        self.active_pokemon_moves = self.organize_moves()
        self.active_pokemon_moves.sort(key=lambda x: x["dmg"], reverse=True)
        self.opponent_pokemon_type = self.get_opponent_pokemon_type()

        for x in self.active_pokemon_moves:
            if x["name"] in ["toxic", "willowisp", "thunderwave", "sleeppowder"]:
                self.status_move_usable = True

        if self.get_opponent_pokemon_status():
            return self.ws.send(f"{self.room}|/move {self.best}")

        weaknesses = self.get_type_effectiveness(self.opponent_pokemon_type)

        weaknesses_ = {}
        for x in self.active_pokemon_moves:
            name = x["name"]
            # removing the keys
            # ex: {"counter": {"water": "normal", "electric": "normal"}}
            # it's now {"counter": ["normal", "normal"]}
            weaknesses_[name] = list(weaknesses[name].values())

        w_ = self.get_effectiveness(weaknesses_)

        self.best = max(w_, key=lambda x: w_[x])

        if "choice" in self.team[self.active_pokemon]["item"] and self.choice_band == "":
            self.choice_band = self.best

        return self.ws.send(f"{self.room}|/move {self.best}")
