# The following code was provided as part of a project.
# As such, please refer to the project's LICENSE file.
# If no such file was included, then no LICENSE was granted,
# meaning that all usage was against the author's will.
#
# In applicable cases, the author reserves themself the right
# to legally challenge any uses that are against their will,
# or goes against the LICENSE.
#
# Only through a written agreement designating the user
# (be it physical person or company) by name from the author
# may the terms of the LICENSE, or lack thereof, be changed.
#
# Author: Alex SHP <alex.shp38540@gmail.com>
import warnings
from abc import ABC, abstractmethod
import random
from typing import Type, Callable, Optional, Union
import re

from .utils import ansi_skipping_len, clean_re

missing = object()

Number = int | float
P_FIELD = dict[Number, float]
ExecutionResult = tuple[Number, P_FIELD]
OPERATION = Callable[[Number, Number], Number]
PUBLISHER_T = Callable[[str], None]

CRITICAL_DICE_PERM = []
CRITICAL_DICE_TMP = []


def combine(d1: P_FIELD, d2: P_FIELD, operation: OPERATION):
    result: dict[Number, float] = {}
    for v1 in d1:
        for v2 in d2:
            y = operation(v1, v2)
            if y not in result:
                result[y] = d1[v1] * d2[v2]
            else:
                result[y] += d1[v1] * d2[v2]
    return result


class Node(ABC):
    __children__: dict[re.Pattern, Type['Node']] = {}
    is_value: False
    priority_modifier: int = 4
    """
    A modifier of the priority of the node, should be less than 10, more than 0
    """

    def __init__(self, expression: str, base_priority: int = 0):
        self._probas: P_FIELD | None = None
        self.expression = expression
        self.base_priority = base_priority
        self.last_value = None
        self.left_child: Optional[Node] = None
        self.right_child: Optional[Node] = None
        self._solved = False

    def __init_subclass__(
            cls,
            command: str = missing,
    ):
        if command is missing:
            raise ValueError(
                'Missing the value required to determine which actions to take. '
                f'Please pass, when defining {cls.__name__}, '
                'the kwargs "command" or "commands" with the name of the command'
            )
        if cls.priority_modifier >= 10:
            warnings.warn(f"Priority offset is more than 10 ({cls.priority_modifier}). "
                          f"This may cause the compiler to override the parenthesis arround this object")
        elif cls.priority_modifier < 0:
            raise ValueError(
                f"Cannot accept negative priority modifier for {cls.__name__} ({cls.priority_modifier}"
            )

        # print(command)
        cls.__children__[re.compile(command)] = cls

    def expected_value(self):
        if not self._solved:
            raise ValueError('Required expected value before running the node')
        return (
            sum(
                [
                    s * self._probas[s] for s in self._probas
                ]
            ) / len(self._probas)
            if len(self._probas) > 0 else 0.
        )

    def run(self, add_msg_discord: PUBLISHER_T = None) -> ExecutionResult:
        l_value, l_probas = self.left_child.run()
        r_value, r_probas = self.right_child.run()
        self.last_value = self._op(l_value, r_value)
        self._solved = True
        if self._probas is None:
            self._probas = self.combine(l_probas, r_probas)
        return self.last_value, self._probas

    @abstractmethod
    def _op(self, left: Number, right: Number) -> Number:
        """
        This method defines the behavior of the operator.
        It will normally be called first to get the
        resulting value, then the values of all probabilities.
        """
        raise NotImplementedError

    def combine(self, d1: P_FIELD, d2: P_FIELD) -> P_FIELD:
        return combine(d1, d2, self._op)

    def _to_str(self) -> tuple[list[str], int]:
        if self.is_value:
            return ["\033[32;1m" + self.expression + "\033[0m"], len(self.expression)
        else:
            offset = 0

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
                l_lines[i] + " " * (
                        start_left - ansi_skipping_len(l_lines[i])
                ) + r_lines[i]
                for i in range(depth)
            ]

            return [head_line] + lines, offset

    def __str__(self):
        lines, _ = self._to_str()
        t = "-" * 63 + "\n\tParsing Tree:\n\n"
        for line in lines:
            t += line + "\n"
        return t + "- " * 32

    @classmethod
    def make(cls, expression: str, base_priority: int = 0) -> "Node":
        for pattern, subclass in cls.__children__.items():
            if pattern.match(expression):
                # print(f"Matched {subclass.__name__} for {expression}")
                return subclass(expression, base_priority)
        raise KeyError(
            f"Could not find any node type to match symbol {expression}. "
            f"Please check the spelling.\n"
            f"Valid symbols include:\n\t[" +
            ", ".join(
                (
                    ['', '', '', '', '\n\t'][i % 5] # newline for readability
                    +
                    repr(clean_re(patt))
                )
                for i, patt in enumerate(cls.__children__)
                if clean_re(patt)
            )
            + "]"
        )

    def count_dices_children(self) -> int:
        if isinstance(self, DiceNode):
            return 1
        count = 0
        if self.left_child is not None:
            count += self.left_child.count_dices_children()
        if self.right_child is not None:
            count += self.right_child.count_dices_children()
        return count

    def first_die_child(self) -> Union['DiceNode', None]:
        if isinstance(self, DiceNode):
            return self
        dn = None
        if self.left_child is not None:
            dn = self.left_child.first_die_child()
        if dn is not None:
            return dn
        return self.right_child.first_die_child()

    @property
    def probas(self):
        return self._probas.copy()

    @property
    def is_value(self):
        return isinstance(self, ValueNode) or isinstance(self, DiceNode)

    def __add__(self, other: 'Node'):
        if not isinstance(other, Node):
            raise TypeError(f"Expected a Node, got {other.__class__.__name__}")
        # print(
        #     f"{self.expression}: {self.priority}. {other.expression}: {other.priority}"
        # )
        if self.is_value and not other.is_value:
            # self is the left side of an operation
            other.left_child = self
            return other
        elif not self.is_value:
            # Self is an operation. Two choices here.
            # Either other is a less prioritized operation, in which case self should be its leftmost child
            # or other is more prioritized and should be a child of self

            if other.priority > self.priority:
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

    @property
    def priority(self):
        return self.base_priority + self.priority_modifier


def node(symbol: str, strict: bool = True, priority_modifier: int = 4) -> Callable[[OPERATION], Type[Node]]:
    """
    Converts a simple function into a node

    Parameters:
    -----------
    symbol: str
        The symbol that matches this node type

    strict: bool
        Whether that symbole is to be matched strictly.
        If set to false, then the symbol "+" may be matched by "+-".
        Defaults to True.

    Examples:
    ---------
        In the following example

        >>> @node('hi')
        >>> def op(x: int, y: int) -> int:
        ...    return x + y

        A new node_type 'hi' will be created.
        Using the command '1 hi 2' in dices will return 3.

    """
    if strict:
        for sc in [
            "\\", "|"
                  ".", "^", "$", "*",
            "+", "?", "{", '}',
            "(", ")", "[", "]"
        ]:
            symbol = symbol.replace(sc, f"\\{sc}")
        if not symbol.startswith('^'):
            symbol = "^" + symbol
        if not symbol.endswith('$'):
            symbol += '$'

    pm = priority_modifier

    def __wrapped__(operation: OPERATION):
        class GeneratedNodeType(Node, command=symbol):
            priority_modifier = pm

            def _op(self, left: Number, right: Number) -> Number:
                return operation(left, right)

        GeneratedNodeType.__name__ = operation.__name__
        # print(f"Generated {GeneratedNodeType=} with {symbol=}")
        return GeneratedNodeType

    return __wrapped__


class ValueNode(Node, command=r'\d+$'):
    priority_modifier = 0

    def combine(self, d1: P_FIELD, d2: P_FIELD) -> P_FIELD:
        raise ValueError('Call to combine on dice cannot work')

    def _op(self, left: Number, right: Number) -> Number:
        raise ValueError("Call to _op done when should not have happened")

    def run(self, add_msg_discord=None) -> ExecutionResult:
        self.last_value = int(self.expression)
        self._probas = {self.last_value: 1}
        self._solved = True
        return self.last_value, self._probas


class DiceNode(Node, command=r'\d*d\d+$'):
    priority_modifier = 0

    def __init__(self, expression: str, base_priority: int = 0):
        super().__init__(expression, base_priority)
        number, size = self.expression.split('d')
        if not number:
            number = "1"
        self.number, self.size = int(number), int(size)
        reduced = f'd{size}'
        self._critical = reduced in CRITICAL_DICE_PERM or reduced in CRITICAL_DICE_TMP

    def combine(self, d1: P_FIELD, d2: P_FIELD) -> P_FIELD:
        raise ValueError('Call to combine on dice cannot work')

    def _op(self, left: Number, right: Number) -> Number:
        raise ValueError("Call to _op done when should not have happened")

    def _set_probas(self):
        base_proba = {
            i + 1: 1 / self.size
            for i in range(self.size)
        }
        proba = {0: 1.}
        for i in range(self.number):
            proba = combine(base_proba, proba, lambda x, y: x + y)
        self._probas = proba

    def run(self, add_msg_discord=None) -> ExecutionResult:
        if self._probas is None:
            self._set_probas()
        value = 0
        for i in range(self.number):
            value += (dice_roll := random.randint(1, self.size))
            if self._critical and (dice_roll == 1 or dice_roll == self.size):
                if dice_roll == 1:
                    print(f"\033[33mDice {i} (of the {self.expression}) rolled a \033[31;1mNATURAL 1\033[33m "
                          f"which is a critical failure\033[0m")
                    if add_msg_discord is not None:
                        add_msg_discord(f"Dice {i} (of the {self.expression}) rolled a **NATURAL 1** "
                                        f"which is a **critical failure**")
                elif dice_roll == self.size:
                    print(f"\033[33mDice {i} (of the {self.expression}) rolled a "
                          f"\033[32;1mNATURAL {self.size}\033[33m which is a critical success\033[0m")
                    if add_msg_discord is not None:
                        add_msg_discord(f"Dice {i} (of the {self.expression}) rolled a **NATURAL {self.size}** "
                                        f"which is a **critical success**")
        self.last_value = value
        self._solved = True
        return self.last_value, self._probas
