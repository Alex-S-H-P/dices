import builtins
import json
import logging
import pickle
import typing
from fight_back import Participant, Fight

DISPLAY, PLAY, INPUT = 0, 1, 2


class Display:

    def __init__(self, fight):
        self.mode = INPUT
        self.fight: Fight = fight


def index(ls: list, element) -> int:
    for i, e in enumerate(ls):
        if e == element:
            return i


def next_instruction_is(instruction: list[str], head: int, value: str) -> bool:
    if head + 1 < len(instruction):
        return instruction[head + 1] == value
    return False


# we have here the functionalities of the system
Operation = typing.NewType("Operation", typing.Callable[[list[str], Display], str])


def add_participant(instruction: list[str], display: Display) -> str:
    """Adds a player to the field"""
    head: int = 1
    name = "Unnamed"
    pv = -1
    ac = -1
    while head < len(instruction):
        if instruction[head][-2:] not in ["pv", "ac"] and name == "Unnamed":
            name = instruction[head]
            head += 1
        elif instruction[head][-2:] == "pv" and pv < 0:
            pv = int(instruction[head][:-2])
            head += 1
        elif next_instruction_is(instruction, head, "pv") and pv < 0:
            pv = int(instruction[head])
            head += 2
        elif instruction[head][-2:] == "ac" and ac < 0:
            ac = int(instruction[head][:-2])
            head += 1
        elif next_instruction_is(instruction, head, "ac") and ac < 0:
            ac = int(instruction[head])
            head += 2
        else:
            return f"ERR : could not decipher instructions for new fighter. " \
                   "Please use 'add name 18pv 36ac' for example {instruction}, {head} "
        if ac > 0 and pv > 0 and name:
            display.fight.add(Participant(PV=pv, AC=ac, name=name), initiative=0)
            return "OK : fighter added !"
    return "ERR : missed a few arguments. Please use 'add name 18pv 36ac' for example"


def set_initiative(instruction: list[len], display: Display):
    """sets the initiative of a player by name.
    If multiple players are found, then does so on the one with the lowest initiative"""
    head = 1
    name = instruction[head]
    head += 1
    initiative = int(instruction[head])
    fighter: Participant
    for fighter in reversed(display.fight):
        if fighter.name == name:
            bracket = display.fight.participants[fighter.initiative]
            i = index(bracket, fighter)
            bracket.pop(i)
            display.fight.add(fighter, initiative)
    return f"OK : set the initiative of {name} at {initiative}"


def save(instruction: list[str], display: Display):
    path = instruction[1] + ".fight"
    # TODO ask about overwriting a file
    pickle.dump(display.fight, open(path, "wb"))
    return "OK : Fight stored"


def load(instruction: list[str], display: Display):
    path = instruction[1] + ".fight"
    new_fight = pickle.load(open(path, "rb"))
    if len(display.fight) > 0:
        for fighter in new_fight:
            display.fight.add(fighter, fighter.initiative)
        return f"OK : Added {len(new_fight)} new participants"
    else:
        display.fight = new_fight
        return "OK : Fight restored"


def add_status(instruction: list[str], display: Display):
    head = 1
    name = instruction[head]
    head += 1
    status = instruction[head]
    fighter: Participant
    for fighter in reversed(display.fight):
        if fighter.name == name:
            fighter.status.append(status)


func_map: dict[str, Operation] = {"add_participant": add_participant, "initiative": set_initiative,
                                  "set_initiative": set_initiative,
                                  "save": save, "add_status": add_status, "load": load}
