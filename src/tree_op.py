import random
import typing


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


class node:

    def __init__(self, is_value: bool = None, expression: str = "0", base_priority: int = 0):
        self.expression = expression
        self.is_value = is_value if is_value is not None else True
        self.defaulted = is_value is None
        self.left_child: typing.Optional[node] = None
        self.right_child: typing.Optional[node] = None
        self.solved = False
        self.value: int = 0
        self.max: int = 0
        self.avg: float = 0.
        self._base_priority = base_priority

    def solve(self) -> tuple[int, int, float]:
        if self.solved:
            return self.value, self.max, self.avg
        if self.is_value:
            if "d" in self.expression:
                fragments = self.expression.split("d")
                multi = int(fragments[0])
                size = int(fragments[1])
                for i in range(multi):
                    self.value += random.randint(1, size)
                    self.max += size
                    self.avg += (size + 1) / 2
                self.solved = True
            else:
                self.value = int(self.expression)
                self.max = self.value
                self.avg = float(self.value)
                self.solved = True
        else:
            # this node is an operator
            if self.expression == "*":
                self.value: int = 1
                self.max: int = 1
                self.avg: float = 1.
                for c in self.children:
                    v, m, a = c.solve()
                    self.value *= v
                    self.max *= m
                    self.avg *= a
            elif self.expression == "/":
                self.value, self.max, self.avg = self.children[0].solve()
                for c in self.children[1:]:
                    v, m, a = c.solve()
                    self.value = self.value // v
                    self.max = self.max // m
                    self.avg = self.avg / a
            elif self.expression == "+":
                for c in self.children:
                    v, m, a = c.solve()
                    self.value += v
                    self.max += m
                    self.avg += a
            elif self.expression == "-":
                self.value, self.max, self.avg = self.children[0].solve()
                for c in self.children[1:]:
                    v, m, a = c.solve()
                    self.value -= v
                    self.max -= m
                    self.avg -= a
        return self.value, self.max, self.avg

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
            return ["\033[32;1m"+self.expression+"\033[0m"], len(self.expression)
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
