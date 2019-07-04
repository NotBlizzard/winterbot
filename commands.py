import json
import re
import random
import time
import subprocess
import platform
import humanize


def permission(rank):
    def wrap_(function):
        def wrapper(*args):
            try:
                permissions = json.loads(open("./permissions.json", "r").read())
                user = args[2]

                if int(permissions[user]) == 0:
                    return False

                if int(permissions[user]) >= rank:
                    return function(*args)

            except FileNotFoundError:
                open("./permissions.json", "w+").write("{}")
                return False
            except KeyError:
                if rank == 1:
                    return function(*args)
                else:
                    return False
            finally:
                pass
        return wrapper

    return wrap_


@permission(1)
def command_pick(args, room, user, bot):
    return random.choice(args)


@permission(4)
def command_say(args, room, user, bot):
    return ' '.join(args)


@permission(1)
def command_random(args, room, user, bot):
    return "4 // chosen by a fair dice roll"


@permission(4)
def command_node(args, room, user, bot):
    node = subprocess.getoutput("node -e \"console.log({})\"".format(' '.join(args)))
    node = re.sub(r'\n', '', node)
    return node


@permission(4)
def command_setrank(args, room, user, bot):
    if int(args[1]) > 4 or int(args[1]) < 0:
        return "Rank cannot be more than 4, and less than 0."

    old_data = json.loads(open("./permissions.json", "r").read())
    data = open("./permissions.json", "w+")
    old_data[args[0]] = args[1]
    data.write(json.dumps(old_data))
    return "Ranks updated."


@permission(4)
def command_hotpatch(args, room, user, bot):
    return bot.hotpatch(args[0])

@permission(1)
def command_pythonversion(args, room, user, bot):
    return platform.python_version()

@permission(1)
def command_uptime(args, room, user, bot):
    return humanize.naturaltime(time.time() - bot.starttime)[:-4]

@permission(4)
def command_eval(args, room, user, bot):
    try:
        if room[0:6] == "battle":
            battle = bot.battles[room]
            exec("self=battle;result={}".format(" ".join(args)), locals(), globals())
        else:
            exec("self=bot;result={}".format(" ".join(args)), locals(), globals())
        return result
    except:
        pass
