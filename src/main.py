import re
import typing

import discord
import dices
import errors
import sys

call = typing.Callable[[str, ...], None]

things_to_say: list[tuple[str, str]] = []


def say(thing: str) -> None:
    things_to_say.append((thing, ""))


def to(chan: str) -> None:
    if len(things_to_say) > 0:
        things_to_say[-1] = things_to_say[-1][0], chan


intents = discord.Intents.default()
intents.message_content = True


client = discord.Client(intents=intents)
d_probas: dict[int, dict] = {}
d_value: dict[int, float] = {}

say_command: list[str] = ["say", "--say", "-s", "tell", "write", "print"]
to_command: list[str] = ["to", "--to", "-t", ]
specific_command_types: list[typing.Union[list[tuple[call, int], str]]] = [
    [(say, 1)] + say_command,
    [(to, 1)] + to_command
]

commands: dict[str, tuple[call, int]] = {}
for command_type in specific_command_types:
    cmd = command_type[0]
    for command in command_type[1:]:
        commands[command] = cmd


def clean(txt: str) -> str:
    return re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]').sub("", txt)


@client.event
async def on_ready():
    print(f"Logged in successfully as {client.user}",
          f"\n\t{things_to_say}" if len(things_to_say) > 0 else
          "", sep="")

    for thing in things_to_say:
        print(f"Trying to say {thing[0]}",
              f" to {thing[1]}" if thing[1] else ".", sep="")
        for server in client.guilds:
            for channel in server.text_channels:
                print(f"\tLooking at channel {channel.name} of server {server.name}")
                if (
                    (not thing[1] or server.name == thing[1])
                    and
                    "test-bots" in channel.name
                ) or channel.name == thing[1]:
                    print("\t\tMatched !")
                    await client.get_channel(channel.id).send(thing[0])


@client.event
async def on_message(message: discord.Message):
    # print(message.__class__.__name__, message.channel.__class__.__name__, (id := message.channel.id))
    chan_id = message.channel.id
    global d_probas, d_value
    # quick and dirty way to ensure thatclient. context persists
    message_pile: list[str] = []

    def pre_add_message(x: str, chan):
        client.loop.create_task(chan.send(x))

    if message.author == client.user:
        return
    elif message.content.startswith("$"):

        try:
            val = 0.
            prob = {}
            if chan_id in d_value:
                val = d_value[chan_id]
            if chan_id in d_probas:
                prob = d_probas[chan_id]
            channel = message.channel

            def add_message(x: str):
                pre_add_message(x, channel)

            answer, probas, value = await dices.discord_main(
                message.content[1:], prob, val, to_send_to=add_message,
                channel=channel
            )
            d_value[chan_id] = value
            d_probas[chan_id] = probas
        except errors.ShutDownCommand as er:
            await message.channel.send("GoodBye !")
            raise er
        except Exception as e:
            print(e)
            raise e
        print(answer)
        print(message_pile)
        for msg in message_pile:
            await message.channel.send(msg)
        await message.channel.send(clean(answer) + (")" if answer.count("(") > answer.count(")") else ""))


if __name__ == '__main__':
    pointer: int = 1
    while len(sys.argv) > pointer:
        print(sys.argv, sys.argv[pointer], "found" if sys.argv[pointer] in say_command else "not found")
        cur_arg = sys.argv[pointer]
        cmd = commands[cur_arg]
        if cur_arg in commands and pointer + cmd[1] < len(sys.argv):
            print(cmd)
            print(sys.argv[pointer + 1:], sys.argv[:pointer + cmd[1]])
            cmd[0](
                *(sys.argv[pointer + 1:pointer + cmd[1] + 1]
                  if cmd[1] > 0
                  else []
                  )
            )  # we load the sys.argv into the right arguments

            pointer += cmd[1]
        pointer += 1
    client.run(open("./key.key", "r").read())
