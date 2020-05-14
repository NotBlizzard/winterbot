import json
import re
import random
import time
import subprocess
import platform
import humanize
import requests
import os


def permission(rank):
    def wrap_(function):
        def wrapper(*args):
            try:
                permissions = json.loads(open("permissions.json", "r").read())
                user = args[2]

                if int(permissions[user]) == 0:
                    return False

                if int(permissions[user]) >= rank:
                    return function(*args)

            except FileNotFoundError:
                open("permissions.json", "w").write("{}")
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


@permission(1)
def command_dadjoke(args, room, user, bot):
    headers = {"Accept": "application/json"}
    data = requests.get("https://icanhazdadjoke.com", headers=headers)
    return data.json()["joke"]


@permission(1)
def command_catfact(args, room, user, bot):
    data = requests.get("https://cat-fact.herokuapp.com/facts")
    return random.choice(data.json()["all"])["text"]


@permission(4)
def command_say(args, room, user, bot):
    return ' '.join(args)


@permission(1)
def command_owo(args, room, user, bot):
    args = " ".join(args)
    args = re.sub(r'(r|l|w)', "w", args)
    args = re.sub(r'n(?=a|e|i|o|u)', "ny", args)
    return args


@permission(4)
def command_node(args, room, user, bot):
    node = subprocess.getoutput(f"node -e \"console.log({' '.join(args)})\"")
    node = re.sub(r'\n', '', node)
    return node


@permission(4)
def command_setrank(args, room, user, bot):
    if int(args[1]) > 4 or int(args[1]) < 0:
        return "Rank cannot be more than 4, and less than 0."

    old_data = json.loads(open("./permissions.json", "r").read())
    data = open("permissions.json", "w")
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


@permission(1)
def command_define(args, room, user, bot):
    headers = {"Authorization": f"Token {os.getenv('OWLBOT')}"}
    url = f"https://owlbot.info/api/v3/dictionary/{args[0]}"
    data_ = requests.get(url, headers=headers)
    return data_.json()['definitions'][0]['definition']


@permission(4)
def command_eval(args, room, user, bot):
    try:
        locals_ = locals()
        exec(f"self=bot;result={' '.join(args)}", globals(), locals_)
        return locals_["result"]
    except Exception as e:
        print(e)
