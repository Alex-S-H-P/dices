import random
import typing
from operator import xor

import numpy as np

ADVANTAGE_TOKEN = ["adv", "avantage", "av", "max"]
DISADVANTAGE_TOKEN = ["disadv", "dadv", "désavantage", "desavantage", "dav", "min"]
DROP_TOKEN = ["drop"]
CRITICAL_DICE_PERM = []
CRITICAL_DICE_TMP = []


def p_len(s: str) -> int:
    """Because the length of an ANSI containing string is a bore..."""
    ANSI = False
    count = 0
    for char in s:
        if char == "\033":
            ANSI = True
        elif not ANSI:
            count += 1
        elif ANSI and char == "m":
            ANSI = False
    return count


def combine(d1: dict[int, float], d2: dict[int, float], op: typing.Callable):
    result: dict[int, float] = {}
    for v1 in d1:
        for v2 in d2:
            y = op(v1, v2)
            if y not in result:
                result[y] = d1[v1] * d2[v2]
            else:
                result[y] += d1[v1] * d2[v2]
    return result


def combinations(n_iter: int, max_n: int, min_n: int = 1) -> typing.Iterable:
    cur_list = [min_n] * n_iter
    while cur_list[0] <= max_n:
        yield cur_list
        pointer = -1
        cur_list[pointer] += 1
        while cur_list[pointer] > max_n and pointer > -n_iter:
            cur_list[pointer] = min_n
            pointer -= 1
            cur_list[pointer] += 1


def _handleComparaison(expression: str, left_child, right_child, add_msg_discord=None) -> tuple[int, dict[int, float]]:
    """
    Handles the comparator expression.

    * If the one side is a die value, counts the amount of dices that compare to the other value according to the operator.
    * In any other cases, returns 1 if the values compare according to the operator.
    """
    # type safeties
    if expression not in (">", "<", "<=", ">=", "=", "==", "!="):
        raise ValueError(f"Unexpected comparator expression {expression}")
    gt = expression == ">"
    if left_child is None or right_child is None:
        raise ValueError(f"Comparator is alone and cannot work thusly")
    # ensuring whether each value is a type
    left_is_die = left_child.is_value and "d" in left_child.expression.lower()
    right_is_die = right_child.is_value and "d" in right_child.expression.lower()
    # ensuring that the comp_function is valid
    comp_func = {">": lambda x, y : int(x > y),
                 "<": lambda x, y : int(x <y ),
                 "<=" : lambda x, y :int(x <= y),
                 ">=" : lambda x, y: int(x >= y),
                 "=": lambda x, y: int(x==y),
                 "==": lambda x, y: int(x==y),
                 "!=": lambda x, y:int(x != y)}[expression]

    # Are we in the first use case ?
    if xor(left_is_die, right_is_die):  # if one and only one of the sides is a die
        # shuffle the values
        die_child = left_child if left_is_die else right_child
        other_child = left_child if right_is_die else right_child

        # read the die
        if die_child.expression[0] == "d":
            die_child.expression = "1" + die_child.expression
        fragments = die_child.expression.split("d")
        assert len(fragments) == 2, f"Unreadable dice expression : {die_child.expression}.\n" \
                                    f"Try to write a value like 2d6 with 2 the number of dice " \
                                    f"and 6 the amount of faces on each die"
        multi, size = int(fragments[0]), int(fragments[1])

        # read the other value
        v2 = other_child.solve(add_msg_discord)
        proba2 = other_child.probas

        # roll the dice
        probas = {0: 1.}
        value = 0  # by default, no comparison succeeded.
        die_proba: dict[int, float] = {i: 1 / size for i in range(1, size + 1)}
        for i in range(multi):

            # update the value and the proba
            value += comp_func(dice_roll := random.randint(1, size), v2)
            probas = combine(probas,
                             combine(die_proba, proba2, comp_func),
                             lambda x, y: x + y)  # we add to the stat the probas of having the comparison succeed

            # handle critical rolls
            if "d" + str(size) in CRITICAL_DICE_PERM + CRITICAL_DICE_TMP:
                if dice_roll == 1:
                    print(f"\033[33mDice {i} (of the {die_child.expression}) rolled a \033[31;1mNATURAL 1\033[33m "
                          f"which is a critical failure\033[0m")
                    if add_msg_discord is not None:
                        add_msg_discord(f"Dice {i} (of the {die_child.expression}) rolled a **NATURAL 1** "
                                        f"which is a **critical failure**")
                elif dice_roll == size:
                    print(f"\033[33mDice {i} (of the {die_child.expression}) rolled a "
                          f"\033[32;1mNATURAL {size}\033[33m which is a critical success\033[0m")
                    if add_msg_discord is not None:
                        add_msg_discord(f"Dice {i} (of the {die_child.expression}) rolled a **NATURAL {size}** "
                                        f"which is a **critical success**")
        return value, probas
    else:
        v1, v2 = left_child.solve(add_msg_discord), right_child.solve(add_msg_discord)
        probas = combine(left_child.probas, right_child.probas, op=comp_func)
        return 1 if comp_func(v1, v2) else 0, probas
    pass


class node:

    def __init__(self, is_value: bool = None, expression: str = "0", base_priority: int = 0):
        self.expression = expression
        if self.expression in ADVANTAGE_TOKEN:
            self.expression = ADVANTAGE_TOKEN[0]
        elif self.expression in DISADVANTAGE_TOKEN:
            self.expression = DISADVANTAGE_TOKEN[0]
        elif self.expression in DROP_TOKEN:
            self.expression = DROP_TOKEN[0]
        self.is_value = is_value if is_value is not None else True
        self.defaulted = is_value is None
        self.left_child: typing.Optional[node] = None
        self.right_child: typing.Optional[node] = None
        self.solved = False
        self.value: int = 0
        self.probas: dict[int, float] = {}
        self._base_priority = base_priority

    def expected_value(self):
        if not self.solved:
            self.solve()
        return sum([s * self.probas[s] for s in self.probas]) / len(self.probas) if len(self.probas) > 0 else 0.

    def solve(self, add_msg_discord=None) -> int:
        if self.solved:
            return self.value
        if self.is_value:
            if "d" in self.expression:
                if self.expression[0] == "d":
                    self.expression = "1" + self.expression
                fragments = self.expression.split("d")
                self.value = 0
                multi = int(fragments[0])
                size = int(fragments[1])
                self.probas = {0: 1.}
                die_proba: dict[int, float] = {i: 1 / size for i in range(1, size + 1)}
                for i in range(multi):
                    self.value += (dice_roll := random.randint(1, size))
                    self.probas = combine(self.probas, die_proba, lambda x, y: x + y)
                    if "d" + str(size) in CRITICAL_DICE_PERM + CRITICAL_DICE_TMP:
                        if dice_roll == 1:
                            print(f"\033[33mDice {i} (of the {self.expression}) rolled a \033[31;1mNATURAL 1\033[33m "
                                  f"which is a critical failure\033[0m")
                            if add_msg_discord is not None:
                                add_msg_discord(f"Dice {i} (of the {self.expression}) rolled a **NATURAL 1** "
                                                f"which is a **critical failure**")
                                print("reached")
                        elif dice_roll == size:
                            print(f"\033[33mDice {i} (of the {self.expression}) rolled a "
                                  f"\033[32;1mNATURAL {size}\033[33m which is a critical success\033[0m")
                            if add_msg_discord is not None:
                                add_msg_discord(f"Dice {i} (of the {self.expression}) rolled a **NATURAL {size}** "
                                                        f"which is a **critical success**")
                                print("reached")
                self.solved = True
            else:
                self.value = int(self.expression)
                self.probas = {self.value: 1}
                self.solved = True
        else:
            # this node is an operator
            if self.expression == "*":
                self.value: int = 1
                self.probas = {1: 1.}
                for c in self.children:
                    v = c.solve()
                    self.probas = combine(self.probas, c.probas, op=lambda x, y: x * y)
                    self.value *= v
            elif self.expression == "/":
                self.value = self.left_child.solve() // self.right_child.solve()
                self.probas = combine(self.left_child.probas, self.right_child.probas, op=lambda x, y: x // y)
            elif self.expression == "+":
                self.value = (self.left_child.solve() if self.left_child is not None else 0) + self.right_child.solve()
                self.probas = combine(self.left_child.probas, self.right_child.probas, op=lambda x, y: x + y)
            elif self.expression == "-":
                if self.left_child is None:
                    self.value = -self.right_child.solve()
                else:
                    self.value = self.left_child.solve() - self.right_child.solve()
                self.probas = combine(self.left_child.probas, self.right_child.probas, op=lambda x, y: x - y)
            elif self.expression == ADVANTAGE_TOKEN[0]:
                self.probas = {-2 ** 31: 1.}
                self.value = -2 ** 31
                if self.left_child is not None:
                    repeats = self.left_child.solve()
                else:
                    repeats = 2
                for _ in range(repeats):
                    self.value = max(self.right_child.solve(), self.value)
                    # print("repeat", self.value, self.right_child.value, repeats, _)
                    self.probas = combine(self.right_child.probas, self.probas, op=lambda x, y: max(x, y))
                    self.right_child.solved = False  # we want independent dice rolls
                    self.right_child.value = 0
            elif self.expression == DISADVANTAGE_TOKEN[0]:
                self.probas = {2 ** 31: 1.}
                self.value = 2 ** 31
                if self.left_child is not None:
                    repeats = self.left_child.solve()
                else:
                    repeats = 2
                for _ in range(repeats):
                    self.value = min(self.right_child.solve(), self.value)
                    # print("repeat", self.value, self.right_child.value, repeats, _)
                    self.probas = combine(self.right_child.probas, self.probas, op=lambda x, y: min(x, y))
                    self.right_child.solved = False  # we want independent dice rolls
                    self.right_child.value = 0
            elif self.expression == DROP_TOKEN[0]:
                # now, a drop command can be used in a few ways...
                # "2d2 drop lowest"  means drop the lowest die.
                # "3d2 drop lowest2" means drop the two lowest dices
                # "2d2 drop highest" means drop the highest die.
                # "drop 2d2" defaults to "2d2 drop lowest"
                lowest: bool = True
                how_many_to_take: int = 1
                size: int = 6
                how_many_to_roll: int = 2
                if self.right_child is None:
                    raise ValueError("Drop commands need an argument on the right to indicate what to drop")
                elif not self.right_child.is_value:
                    raise ValueError("Drop commands cannot have a non value at their direct right")
                elif "highest" in self.right_child.expression or "lowest" in self.right_child.expression:
                    # we are to determine what to drop
                    assert self.right_child.expression.strip("highlowest").__add__("1").isnumeric(), "invalid value" + \
                                                                                                     f"{self.right_child.expression}"
                    if "highest" in self.right_child.expression:
                        lowest = False
                    if len(numbers := self.right_child.expression.strip("highlowest")):
                        how_many_to_take = int(numbers)
                    assert all(config := [
                        self.left_child is not None,
                        len(split := self.left_child.expression.split("d")) <= 2,
                        all([v.isnumeric() for v in split])]), f"invalid parametrized configuration: config {config}"
                    size = int(split[1])
                    how_many_to_roll = int(split[0])
                else:
                    assert all([
                        len(split := self.right_child.expression.split("d")) <= 2,
                        all([v.isnumeric() for v in split]),
                        self.left_child is None]), "invalid die-only configuration"
                    size = int(split[1])
                    how_many_to_roll = int(split[0])
                # starting with all possible dice rolls
                p_dict: dict[tuple[int], float] = dict(
                    [(tuple(comb), 1 / (size ** how_many_to_roll)) for comb in combinations(how_many_to_roll, size)]
                )
                # we take out the ones we don't like and then combine them all
                for combo in p_dict:
                    proba = p_dict[combo]
                    c: list[int] = list(combo)
                    for _ in range(how_many_to_take):
                        if lowest:
                            i = np.argmin(c)
                        else:
                            i = np.argmax(c)
                        c = [C for j, C in enumerate(c) if j != i]
                    s = sum(c)
                    if s in self.probas:
                        self.probas[s] += proba
                    else:
                        self.probas[s] = proba
                # and now we choose a value
                r = random.random()
                sigma = 0
                for k in sorted(list(self.probas.keys())):
                    sigma += self.probas[k]
                    self.value = k
                    if sigma > r:
                        break
            elif self.expression in (">", "<", "<=", ">=", "=", "==", "!="):
                self.value, self.probas = _handleComparaison(self.expression, self.left_child, self.right_child)
        self.solved = True
        return self.value

    @property
    def children(self):
        return [self.left_child if self.left_child is not None else node(),
                self.right_child if self.right_child is not None else node()]

    @property
    def priority(self):
        if self.defaulted:
            return -1  # we don't exist technically
        if self.value:
            return 0 + self._base_priority
        elif self.expression in "+-":
            return 1 + self._base_priority
        elif self.expression in "*/":
            return 2 + self._base_priority
        else:
            return 3 + self._base_priority

    def __add__(self, other):
        assert isinstance(other, self.__class__)
        if self.defaulted:
            # self doesn't exist
            return other
        if self.is_value and not other.is_value:
            # self is the left side of an operation
            other.left_child = self
            return other
        elif not self.is_value:
            # self is an operation. Two choices here.
            # either other is a less prioritized operation, in which case self should be its leftmost child
            # or other is more prioritized and should be a child of self
            if other.priority < self.priority:
                other.left_child = self
                return other
            else:
                if self.right_child is None:
                    self.right_child = other
                else:
                    self.right_child = self.right_child + other
                return self
        else:
            raise Exception("Two side-by side values : {} and {}".format(self.expression, other.expression))

    def _to_str(self) -> tuple[list[str], int]:
        if self.is_value:
            return ["\033[32;1m" + self.expression + "\033[0m"], len(self.expression)
        else:
            offset = 0
            # we are an op . let's check how well we do
            if self.left_child is not None:
                l_lines, offset = self.left_child._to_str()
            else:
                l_lines = []
            head_line = " " * offset + f"\033[34;1m({self.expression})" + "\033[0m"
            offset += len(self.expression) + 2
            start_left = offset
            if self.right_child is not None:
                r_lines, d_offset = self.right_child._to_str()
                offset += d_offset
            else:
                r_lines = []
            depth = max(len(l_lines), len(r_lines))
            l_lines = [l_lines[i] if i < len(l_lines) else "" for i in range(depth)]
            r_lines = [r_lines[i] if i < len(r_lines) else "" for i in range(depth)]
            lines = [
                l_lines[i] + " " * (start_left - p_len(l_lines[i])) + r_lines[i]
                for i in range(depth)
            ]
            return [head_line] + lines, offset

    def __str__(self):
        lines, _ = self._to_str()
        t = "-" * 63 + "\n\tParsing Tree:\n\n"
        for line in lines:
            t += line + "\n"
        return t + "- " * 32
