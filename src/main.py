import re
import discord
import dices
import errors

client = discord.Client()
d_probas: dict[int, dict] = {}
d_value: dict[int, float] = {}


def clean(txt: str) -> str:
    return re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]').sub("", txt)


@client.event
async def on_ready():
    print(f"Logged in successfully as {client.user}")
    for server in client.guilds:
        for channel in server.text_channels:
            if "bots" in channel.name:
                await client.get_channel(channel.id).send("Waking Up !")
                break


@client.event
async def on_message(message):
    # print(message.__class__.__name__, message.channel.__class__.__name__, (id := message.channel.id))
    id = message.channel.id
    global d_probas, d_value
    # quick and dirty way to ensure that context persists
    message_pile = []
    add_message = lambda x: message_pile.append(x)
    if message.author == client.user:
        return
    elif message.content.startswith("$"):
        try:
            val = 0.
            prob = {}
            if id in d_value:
                val = d_value[id]
            if id in d_probas:
                prob = d_probas[id]
            answer, probas, value = dices.discord_main(message.content[1:], prob, val, to_send_to=add_message)
            d_value[id] = value
            d_probas[id] = probas
        except errors.ShutDownCommand as er:
            await message.channel.send("GoodBye !")
            raise er
        except Exception as e:
            print(e)
            raise e
        print(answer)
        for msg in message_pile:
            await message.channel.send(msg)
        await message.channel.send(clean(answer))


if __name__ == '__main__':
    client.run(open("./key.key", "r").read())
