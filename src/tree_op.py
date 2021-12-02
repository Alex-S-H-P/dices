import random
import typing

ADVANTAGE_TOKEN = ["adv", "avantage", "av", "max"]
DISADVANTAGE_TOKEN = ["disadv", "dadv", "désavantage", "desavantage", "dav", "min"]


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
    result = {}
    for v1 in d1:
        for v2 in d2:
            y = op(v1, v2)
            if y not in result:
                result[y] = d1[v1] * d2[v2]
            else:
                result[y] += d1[v1] * d2[v2]
    return result


class node:

    def __init__(self, is_value: bool = None, expression: str = "0", base_priority: int = 0):
        self.expression = expression
        if self.expression in ADVANTAGE_TOKEN:
            self.expression = ADVANTAGE_TOKEN[0]
        if self.expression in DISADVANTAGE_TOKEN:
            self.expression = DISADVANTAGE_TOKEN[0]
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

    def solve(self) -> int:
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
                for i in range(multi):
                    self.value += random.randint(1, size)
                    pb = {}
                    for already_recorded in self.probas:
                        for gotten in range(1, size + 1):
                            if gotten + already_recorded in pb:
                                pb[gotten + already_recorded] += 1 / size * self.probas[already_recorded]
                            else:
                                pb[gotten + already_recorded] = 1 / size * self.probas[already_recorded]
                    self.probas = pb
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
                self.probas = {2**31:1.}
                self.value = 2**31
                if self.left_child is not None:
                    repeats = self.left_child.solve()
                else:
                    repeats = 2
                for _ in range(repeats):
                    self.value = min(self.right_child.solve(), self.value)
                    # print("repeat", self.value, self.right_child.value, repeats, _)
                    self.probas = combine(self.right_child.probas, self.probas, op=lambda x, y: min(x, y))
                    self.right_child.solved = False # we want independent dice rolls
                    self.right_child.value = 0
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
