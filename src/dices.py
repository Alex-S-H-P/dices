import readline

import tree_op
from tree_op import node
import errors

EXIT_INPUTS = ["", "q", "quit", "no", "bye", "exit", "e", "-q", "-e"]
OPERATION_TOKENS = ["+", "-", "*", "/", "(", ")", "|", "#", "&", ">", "<", "<=", ">=", "=", "==", "!="].__add__(
    tree_op.ADVANTAGE_TOKEN + tree_op.DISADVANTAGE_TOKEN + tree_op.DROP_TOKEN
)

FIRST_CHARACTERS_OF_LONG_OPERATION_TOKENS = [token[0] for token in OPERATION_TOKENS if len(token) > 1]

CRITICAL_DICE_PERM = tree_op.CRITICAL_DICE_PERM  # The dices that have a criticality
CRITICAL_DICE_TMP = tree_op.CRITICAL_DICE_TMP
NUM_LINES = 6
INPUTS_THAT_ASK_FOR_GRAPH = ["graph", "draw", "g", "repartition", "see"]
p_len = tree_op.p_len
verbose = True


def _segment(i: str) -> list[str]:
    """Segments an instruction into a series of tokens that are computationable"""
    if verbose:
        print("\033[34m" + "segmenting...\033[0m")
    els = []
    cur = ""

    def partially_fits(string: str) -> bool:
        """Returns true if this string is a substring of any OPERATION TOKEN"""
        return sum([string in token and string != token for token in OPERATION_TOKENS]) != 0

    for idx, char in enumerate(i):
        # print("--", f"'{char}'", cur, els,
        #       char in OPERATION_TOKENS or char == " ",
        #       char in FIRST_CHARACTERS_OF_LONG_OPERATION_TOKENS,
        #       sep="\t\t")
        if char in FIRST_CHARACTERS_OF_LONG_OPERATION_TOKENS:
            if partially_fits(cur + char):
                cur += char
            elif idx + 1 < len(i):
                if sum([char + i[idx + 1] in token for token in OPERATION_TOKENS]) != 0:  # non exclusive partial fit
                    if len(cur) > 0:
                        els.append(cur)
                    cur = char
                elif cur + char in OPERATION_TOKENS:
                    els.append(cur + char)
                    cur = ""
                elif char in OPERATION_TOKENS:
                    if len(cur) > 0:
                        els.append(cur)
                    els.append(char)
                    cur = ""
                else:
                    cur += char
        elif char in OPERATION_TOKENS or char == " ":
            if len(cur) > 0:
                els.append(cur)
                cur = ""
            # If you have a parentheses with no operator beforehand,
            # then the operator is meant to be a multiplication sign (*)
            if len(els) > 0:
                if char == "(" and (els[-1] not in OPERATION_TOKENS):
                    els.append("*")
            if char != " ":
                els.append(char)
                cur = ""
        else:
            # parentheses token
            if len(els) > 0:
                if els[-1] == ")":  # and char not in OPERATION_TOKEN (already verified due to being in the else close)
                    # we have closed a parentheses with no operation on its right side.
                    # By default, this means that the operator is a multiplication (*)
                    els.append("*")
                    # also, because we just added an element in els that is not ")",
                    # the condition is no longer checked, and we won't have any issue
            cur += char
            if cur in OPERATION_TOKENS:
                if not partially_fits(cur):
                    els.append(cur)
                    cur = ""

    if len(cur) > 0:
        els.append(cur)
    return els


def consider_settings(i: list[str]) -> int:
    """Returns true if the token implement settings. Only the first tokens are considered as settings

    Both the pipe ('|') character and the greater than ('>') mean that the setting is to be used only for this time.
    The ampersand character means that the setting is to be kept for the whole session.

    Example :
    crit 1d20 & 1d20
    means make the d20 critical (warns you when you hit either a 1 or a 20) for the whole session
    then roll a d20.
    """
    # most commands won't be setting up anything. Let's have them go
    splitting_tokens = ["|", "#", "&"]
    permanent_tokens = ["&"]
    c = False
    global_parameter_to_set = []
    for token in splitting_tokens:
        if token in i:
            c = True
            # setting up the permanence or no of the command
            if token in permanent_tokens:
                global_parameter_to_set = CRITICAL_DICE_PERM
            else:
                global_parameter_to_set = CRITICAL_DICE_TMP
            break
    if not c:
        return 0
    for idx, token in enumerate(i):
        if token in splitting_tokens:
            return idx + 1
        if token.lower() in ["crits", "crit", "warn", "warns", "critical", "c", "-c"]:
            # we now want to crit.
            # the next token must be a dice (because otherwise we would have just set ourselves for a dnd mode
            NEXT_TOKEN = i[idx + 1]
            assert "d" in NEXT_TOKEN and NEXT_TOKEN[1:].isnumeric()
            global_parameter_to_set.append(NEXT_TOKEN)


def show_P(proba: dict[int, float], roll: int = None) -> str:
    """Should display something like this
      /\
      |
    .3+       ##
      |    ########
      |#################
    0.+----+----+----+--->
      0    5    A    F
    """
    print("graphing: ", locals())
    lines: list[str] = ["" for _ in range(NUM_LINES)]

    def write_at(char: str, _x: int, _y: int) -> None:
        if len(char) > 1:
            for i, c in enumerate(char):
                write_at(c, _x + i, _y)
            return
        if p_len(lines[_y]) <= _x:
            lines[_y] += " " * (_x - p_len(lines[_y])) + char
        else:
            start = None
            end = -1
            for char_idx in range(len(lines[_y])):
                if start is None and p_len(lines[_y][:char_idx]) == _x:
                    start = char_idx
                    end = start + 1
                elif p_len(lines[_y][:char_idx]) == _x:
                    end = char_idx
            # print(lines[y][:start], lines[y][end+1:], start, end, lines[y], x, y, sep="\033[0m||", end="\033[0m\n")
            lines[_y] = lines[_y][:start] + char + lines[_y][end + 1:]

    items, keys = proba.values(), sorted(proba.keys())
    y_max = max(items)
    y_min = min(items)
    if abs(y_min) < 1.:
        y_min = 0
    x_min = min(keys)
    x_max = max(keys)
    n_lines = NUM_LINES - (3 if roll is not None else 2)

    def scale(_y: float) -> int:
        """Approximates the y coordinate in the plane"""
        return int(n_lines * (_y - y_min) / (y_max - y_min) + .5)

    lines[0] = f"\033[36;1m{y_max:.2f}\033[0m"
    n = p_len(lines[0])
    lines[0] += "+\033[33;1m"
    lines[n_lines] = f"\033[36;1m{y_min:.2f}\033[0m+"
    for l_nb in range(1, n_lines):
        lines[l_nb] = " " * n + "|\033[33;1m"
    n += 1
    for x in proba:
        precise_y = proba[x]
        for y in range(scale(precise_y)):
            write_at("#", x + n - x_min, n_lines - 1 - y)
    lines[n_lines] += "-" * (x_max - x_min + n) + "-->"
    lines[n_lines + 1] = "\033[36;1m" + " " * n
    for step in range(x_min, x_max + 5, 5):
        if step != x_min:
            write_at("+", step + n - x_min, n_lines)
        write_at(str(step), step + n - x_min, n_lines + 1)
    # if there is a pointer, print it !
    if roll is not None:
        lines[-1] = " " * (n + roll - x_min) + "\033[32;1m^\033[0m"
    val = ""
    for line in lines:
        val += line + "\n"
    return val


def _decipher(i: list[str], parentheses_priority_offset=10, add_msg_discord=None) -> tuple[
    int, int, float, dict[int, float]]:
    """Renvoie une valeur aléatoire, la valeur maximale et la valeur moyenne à laquelle on pourrait s'attendre
    Operation order : (), *, /, +, -, dice
    Parentheses do not need to be closed
    Parentheses with no operation imply a multiplication (*) """
    i = i[consider_settings(i):]
    print("\033[34m" +
          f"parsing\033[0m... \033[36m{len(i)}\033[0m token{'s' if len(i) > 1 else ''} found : \033[36m{i}\033[0m")
    base_priority = 0
    if len(i) == 0:
        raise SyntaxError("empty command")
    while i[0] in ("(", ")"):
        if i.pop(0) == "(":
            base_priority += parentheses_priority_offset
        else:
            base_priority -= parentheses_priority_offset
    cur_node = node(i[0] not in OPERATION_TOKENS, i[0])
    for token in i[1:]:
        if token in ("(", ")"):
            if token == "(":
                base_priority += parentheses_priority_offset
            else:
                base_priority -= parentheses_priority_offset
            continue
        token_node = node(token not in OPERATION_TOKENS, token, base_priority)
        try:
            cur_node += token_node
        except Exception as e:
            print(cur_node)  # dump the data in the log for debugging purposes
            raise e
    print(cur_node)
    cur_node.solve(add_msg_discord)
    # print(cur_node.probas, sum([k * cur_node.probas[k] for k in cur_node.probas]))
    return (cur_node.solve(add_msg_discord), max(cur_node.probas.keys()),
            sum([k * cur_node.probas[k] for k in cur_node.probas]) if len(cur_node.probas) > 0 else 0,
            cur_node.probas
            )


def decipher(i: str, add_msg_discord=None) -> tuple[int, int, float, dict[int:float]]:
    t: tuple = tuple(_decipher(_segment(i), add_msg_discord=add_msg_discord))
    while len(CRITICAL_DICE_TMP) > 0:
        CRITICAL_DICE_TMP.pop()  # we empty the temp list
    return t


def colorise(value, proba):
    F = getF(proba, value)
    if F > .667:
        return "\033[32;1m" + str(value) + "\033[0m"
    elif F < .333:
        return "\033[31;1m" + str(value) + "\033[0m"
    else:
        return "\033[33;1m" + str(value) + "\033[0m"


def getF(proba, value) -> float:
    return sum(proba[k] for k in proba if k <= value)


def main():
    print("\033[37;1m", "-" * 42, "DICE ENVIRONMENT", "-" * 42, "\033[0m", sep="\n")
    global CRITICAL_DICE_PERM
    P, v = None, None
    while True:
        try:
            input_str = input(">>> ")
        except EOFError:
            print("\n" + "\033[36;1mBye !\033[0m")
            break
        if input_str.lower() in EXIT_INPUTS:
            print("\033[36;1mBye !\033[0m")
            break
        elif (cmd := input_str.lower().split())[0] in INPUTS_THAT_ASK_FOR_GRAPH:
            if P is not None:
                if len(cmd) == 2 and cmd[1].isnumeric():
                    global NUM_LINES
                    NUM_LINES = int(cmd[1])
                show_P(P, v)
            else:
                print("\033[31mCannot graph last dice roll as no dice roll was found in memory\033[0m")
            continue
        elif input_str.lower() in ["dnd", "d&d", "critical", "crit", "dungeon&dragon", "crits", "criticals"
                                                                                                "dungeon & dragon",
                                   "dungeon and dragon", "count crits", "count criticals",
                                   "count critical", "d&d&d&d"]:
            CRITICAL_DICE_PERM.append("d20")
            print("DND mode active. D20s will now announce critical scores")
            continue
        elif input_str.lower() in ["reboot", "rb", "boot", "nocrit"]:
            CRITICAL_DICE_PERM = []
            "Reset"
            print("-" * 63)
            continue
        try:
            v, m, a, P = decipher(input_str)
            print('\tResult :\n\n' +
                  f'Got {colorise(v, P)} (out of \033[36;1m{m}\033[0m maximum, \033[36;1m{a:.2f}\033[0m expected, ' +
                  f'F = \033[36;1m{100 * getF(P, v):.1f}%\033[0m)')
        except Exception as e:
            print(f"\033[31m{e}\033[0m")
        print("-" * 63)


def discord_main(command: str, P=None, v=None, to_send_to=None) -> tuple[str, dict, float]:
    global CRITICAL_DICE_PERM
    if command.lower() in ["", "q", "quit", "no", "bye", "exit", "e", "-q", "-e"]:
        print("\033[36;1mBye !\033[0m")
        raise errors.ShutDownCommand()
    elif (cmd := command.lower().split())[0] in INPUTS_THAT_ASK_FOR_GRAPH:
        if P is not None:
            if len(cmd) == 2 and cmd[1].isnumeric():
                global NUM_LINES
                NUM_LINES = int(cmd[1])
            return show_P(P, v), {}, 0.
        else:
            return "Cannot graph last dice roll as no dice roll was found in memory", {}, 0.
    elif command.lower() in ["dnd", "d&d", "critical", "crit", "dungeon&dragon", "crits", "criticals"
                                                                                          "dungeon & dragon",
                             "dungeon and dragon", "count crits", "count criticals",
                             "count critical", "d&d&d&d"]:
        CRITICAL_DICE_PERM.append("d20")
        return "DND mode active. D20s will now announce critical scores", {}, 0.
    elif command.lower() in ["reboot", "rb", "boot", "nocrit"]:
        CRITICAL_DICE_PERM = []
        return "Reset", {}, 0.
    try:
        v, m, a, P = decipher(command, add_msg_discord=to_send_to)
        return '\tResult :\n\n' + \
               f'Got **{v}** (out of *{m}* maximum, *{a:.2f}* expected, ' + \
               f'**{100 * getF(P, v):.1f}%** lucky', P, v
    except Exception as e:
        print(f"\033[31m{e}\033[0m")
    print("-" * 63)


if __name__ == '__main__':
    main()
