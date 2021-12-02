import sys

from tree_op import node

OPERATION_TOKENS = ["+", "-", "*", "/", "(", ")"]


def erase():
    sys.stdout.write("\033[K")


def upLine():
    sys.stdout.write("\033[F")


def segment(i: str) -> list[str]:
    print("\033[34m" + "segmenting...\033[0m")
    els = []
    cur = ""
    for char in i:
        # print("--", char, cur, els, char in OPERATION_TOKENS or char == " ")
        if char in OPERATION_TOKENS or char == " ":
            # print(char, cur, els, char == " ")
            if len(cur) > 0:
                els.append(cur)
            # If you have a parentheses with no operator beforehand,
            # then the operator is meant to be a multiplication sign (*)
            if len(els) > 0:
                print(char, els[-1], els[-1] not in OPERATION_TOKENS)
                if char == "(" and (els[-1] not in OPERATION_TOKENS):
                    print("defaulting on parentheses")
                    els.append("*")
            if char != " ":
                els.append(char)
            cur = ""
        else:
            if len(els) > 0:
                if els[-1] == ")":  # and char not in OPERATION_TOKEN (already verified due to being in the else close)
                    # we have closed a parentheses with no operation on its right side.
                    # By default, this means that the operator is a multiplication (*)
                    els.append("*")
            cur += char
    if len(cur) > 0:
        els.append(cur)
    return els


def _decipher(i: list[str], parentheses_priority_offset=10) -> tuple[int, int, float]:
    """Renvoie une valeur aléatoire, la valeur maximale et la valeur moyenne à laquelle on pourrait s'attendre
    Operation order : (), *, /, +, -, dice
    Parentheses do not need to be closed
    Parentheses with no operation imply a multiplication (*) """
    print("\033[34m" +
          f"parsing\033[0m, \033[36m{len(i)}\033[0m token{'s' if len(i) > 1 else ''} found : \033[36m{i}\033[0m")
    base_priority = 0
    while i[0] in ("(", ")"):
        if i.pop(0) == "(":
            base_priority += parentheses_priority_offset
        else:
            base_priority -= parentheses_priority_offset
    cur_node = node(i[0] not in OPERATION_TOKENS, i[0])
    token_node = None
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
    return cur_node.solve()


def decipher(i: str) -> tuple[int, int, float]:
    return _decipher(segment(i))


def colorise(value, expected, maximum):
    if value > (expected + maximum) / 2:
        return "\033[32;1m" + str(value) + "\033[0m"
    elif value < 1.5 * expected - maximum / 2:
        return "\033[31;1m" + str(value) + "\033[0m"
    else:
        return "\033[33;1m" + str(value) + "\033[0m"


def main():
    print("\033[37;1m", "-" * 42, "DICE ENVIRONMENT", "-" * 42, "\033[0m", sep="\n")
    while True:
        input_str = input()
        if input_str.lower() in ["", "q", "quit", "no", "bye", "exit", "e", "-q", "-e"]:
            break
        v, m, a = decipher(input_str)
        print('\tResult :\n\n' +
              f'Got {colorise(v, a, m)} (out of \033[36;1m{m}\033[0m maximum, \033[36;1m{a}\033[0m expected)')
        print("-" * 63)


if __name__ == '__main__':
    main()
