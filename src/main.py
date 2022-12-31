import re
import discord
import dices
import errors
import sys


things_to_say : list[str] = []


def say(thing:str)-> None:
    things_to_say.append(thing)

client = discord.Client()
d_probas: dict[int, dict] = {}
d_value: dict[int, float] = {}
say_command : list[str] = ["say", "--say", "-s", "tell", "write", "print"]


def clean(txt: str) -> str:
    return re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]').sub("", txt)


@client.event
async def on_ready():
    print(f"Logged in successfully as {client.user}",
          f"\n\t{things_to_say}" if len(things_to_say) > 0 else
          "", sep="")
    for server in client.guilds:
        for channel in server.text_channels:
            print(f"Looking at the channel {channel.name} of the server {server}")
            if "bots" in channel.name:
                print(f"\tfound channel to print in : {channel.name}")
                for thing in things_to_say:
                    print("\tsaying", thing)
                    await client.get_channel(channel.id).send(thing)
                break


@client.event
async def on_message(message):
    # print(message.__class__.__name__, message.channel.__class__.__name__, (id := message.channel.id))
    chan_id = message.channel.id
    global d_probas, d_value
    # quick and dirty way to ensure thatclient. context persists
    message_pile:list[str] = []

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

            answer, probas, value = dices.discord_main(message.content[1:], prob, val, to_send_to=add_message)
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
    pointer : int  = 1
    print(sys.argv, sys.argv[pointer], "found" if sys.argv[pointer] in say_command else "not found")
    while len(sys.argv) > pointer + 1 and sys.argv[pointer] in say_command:
        things_to_say.append(sys.argv[pointer + 1])
        pointer += 2
    client.run(open("./key.key", "r").read())
