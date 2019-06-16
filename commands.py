import json
import re
import random


def permission(user, rank):
    try:
        permissions = json.loads(open("./permissions.json", "r").read())
        user = re.sub(r"[^A-z0-9]", "", user).lower()
        return int(permissions[user]) >= rank
    except FileNotFoundError:
        open("./permissions.json", "w+").write("{}")
    except KeyError:
        return False
    finally:
        pass


def command_random(args, user, room, ws):
    if permission(user, 3):
        ws.send("{}|{}".format(room, random.choice(args)))


def command_setrank(args, user, room, ws):
    if permission(user, 4):
        old_data = json.loads(open("./permissions.json", "r").read())
        data = open("./permissions.json", "w+")
        old_data[args[0]] = args[1]
        data.write(json.dumps(old_data))
        ws.send("{}|{}".format(room, "Ranks updated."))
        

def command_eval(args, user, room, ws, bot):
    if permission(user, 4):
        try:
            if room[0:6] == "battle":
                battle = bot.battles[room]
                exec("self=battle;result={}".format(" ".join(args)), locals(), globals())
                ws.send("{}|{}".format(room, result))
            else:
                exec("self=bot;result={}".format(" ".join(args)), locals(), globals())
                ws.send("{}|{}".format(room, result))
        except:
            pass
