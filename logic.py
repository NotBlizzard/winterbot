import json
from collections import Counter
from re import sub
import random
from functools import reduce
import configparser

data = configparser.ConfigParser()
data.read("config.ini")
files = data["FILES"]


class Logic:
    """Logic of the Pokemon battles.
       etc. switching, attacking.
    """
    def __init__(self, team, _id, room):
        self.team = team
        self.id = _id
        self.room = room
        self.moves = json.loads(open(files["MOVES"], "r").read().lower())
        self.pokedex = json.loads(open(files["POKEDEX"], "r").read().lower())
        self.typechart = json.loads(open(files["TYPECHART"], "r").read().lower())
        self.active_pokemon_moves = None
        self.status_move_usable = False  # toxic, thunderwave, etc.
        self.opponent_pokemon_status = {}
        self.active_pokemon = None
        self.opponent_pokemon = None
        self.best = ""
        self.best_choice_band_move = ""

    def __str__(self):
        return "<WinterBot Logic>"

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

    def get_if_use_status(self):
        # get status effect of opponent pokemon
        if self.opponent_pokemon not in self.opponent_pokemon_status:
            if self.status_move_usable:
                self.best = [x for x in self.active_pokemon_moves if "status" in x.keys()][0]["name"]
                return True

        return False

    def logic(self, active_pokemon, opponent_pokemon, ws, action):
        self.active_pokemon = active_pokemon
        self.opponent_pokemon = opponent_pokemon
        if self.opponent_pokemon is None:
            return True

        if action == "swap":
            self.team[self.active_pokemon]["fainted"] = True

            self.best_choice_band_move = ""
            for pokemon in self.team:
                if not self.team[pokemon]["fainted"]:
                    # swap to the first non-fainted pokemon in team
                    self.team[pokemon]["active"] = True
                    return ws.send("{}|/switch {}".format(self.room, pokemon))

        if self.best_choice_band_move != "":
            return ws.send("{}|/move {}".format(self.room, self.best_choice_band_move))

        if action in ["tox", "brn", "slp", "par"]:
            self.opponent_pokemon_status[self.opponent_pokemon] = action

        if action == "new move":  # hydro pump
            return ws.send("{}|/move {}".format(self.room, random.choice(self.team[self.active_pokemon]["moves"])))

        self.active_pokemon_moves = self.organize_moves()
        self.active_pokemon_moves.sort(key=lambda x: x["dmg"], reverse=True)
        self.opponent_pokemon_type = self.get_opponent_pokemon_type()

        for x in self.active_pokemon_moves:
            if x["name"] in ["toxic", "willowisp", "thunderwave", "sleeppowder"]:
                self.status_move_usable = True

        if self.get_if_use_status():
            return ws.send("{}|/move {}".format(self.room, self.best))

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

        if "choice" in self.team[self.active_pokemon]["item"] and self.best_choice_band_move == "":
            self.best_choice_band_move = self.best

        return ws.send("{}|/move {}".format(self.room, self.best))
