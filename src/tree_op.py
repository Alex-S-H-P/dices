import random
import typing
from abc import ABC
import numpy as np
from dices_commands.node_actions import ExecutionResult, Number, P_FIELD, ValueNode, DiceNode
from dices_commands.node_actions import Node, node, combine, PUBLISHER_T


ADVANTAGE_TOKEN = ["adv", "avantage", "av", "max"]
DISADVANTAGE_TOKEN = ["disadv", "dadv", "désavantage", "desavantage", "dav", "min"]
EMPHASIS_TOKEN = ["emph", "emphasis"]
DROP_TOKEN = ["drop"]


@node('+', priority_modifier=1)
def add(x: int, y: int):
    return x + y


@node('-', priority_modifier=1)
def sub(x: int, y: int):
    return x - y


@node('*', priority_modifier=3)
def mult(x: int, y: int):
    return x * y


@node('/', priority_modifier=2)
def div(x: int, y: int):
    return x // y


class AdvantageNode(Node, command='(?:' + '|'.join(ADVANTAGE_TOKEN) + ')$'):

    def _op(self, left: Number, right: Number) -> Number:
        return max(left, right)

    def _set_probas(self, l_prob: P_FIELD, r_prob: P_FIELD):
        final = {}
        for repet, p_repet in l_prob.items():
            P = r_prob
            for i in range(repet - 1):
                P = self.combine(r_prob, P)
            for result, p_result in P.items():
                final[result] = final.get(result, 0) + p_result * p_repet
        self._probas = final

    @staticmethod
    def message_about(i: int, add_msg_discord: PUBLISHER_T = None) -> PUBLISHER_T | None:
        if add_msg_discord is None:
            return None
        return lambda s: add_msg_discord(f'Concernant le lancé numéro {i}:\n' + s)

    def run(self, add_msg_discord=None) -> ExecutionResult:
        if self.left_child is None:
            repetitions = 2
            l_probas = {2: 1.}
        else:
            repetitions, l_probas = self.left_child.run(add_msg_discord)
        first_roll, r_probas = self.right_child.run(add_msg_discord)

        if self._probas is None:
            self._set_probas(l_probas, r_probas)

        self.last_value = self._op(
            first_roll,
            *[
                self.right_child.run(self.message_about(i + 1, add_msg_discord))[0]
                for i in range(int(repetitions - .5))
            ]
        )

        return self.last_value, self._probas


class DisadvantageNode(AdvantageNode, command='(?:' + '|'.join(DISADVANTAGE_TOKEN) + ')$'):

    def _op(self, left: Number, right: Number) -> Number:
        return min(left, right)


class EmphasisNode(AdvantageNode, command='(?:' + '|'.join(EMPHASIS_TOKEN) + ')$'):

    def _op(self, left: Number, right: Number) -> Number:

        E = sum([
            k * self.right_child._probas[k]
            for k in self.right_child._probas
        ]) if len(self.right_child._probas) > 0 else 0

        dl = left - E
        dr = right - E
        if abs(dl) >= abs(dr):
            return left
        else:
            return right


class SuperlativeNode(Node, command=r'(?:highest|lowest)\d+'):
    priority_modifier = 0

    def _op(self, left: Number, right: Number) -> Number:
        return 1

    def __init__(self, expression: str, base_priority: int = 0):
        super().__init__(expression, base_priority)
        number = self.expression.removeprefix('lowest').removeprefix('highest')
        if not number:
            self.last_value = 1
        else:
            self.last_value = int(number)
            self._probas = {self.last_value: 1.}
        if self.expression.startswith('lowest'):
            self.last_value *= -1

    def run(self, add_msg_discord: PUBLISHER_T = None) -> ExecutionResult:
        if self._probas is not None:
            return self.last_value, self._probas
        if isinstance(self.right_child, ValueNode):
            value, self._probas = self.right_child.run()
            self.last_value *= value
        return self.last_value, self._probas


class DropNode(Node, command='(?:' + '|'.join(DROP_TOKEN) + ')$'):
    """
    Now, a drop command can be used in a few ways...

    "2d2 drop lowest" means drop the lowest die.
    "3d2 drop lowest2" means drop the two lowest dices
    "2d2 drop highest" means drop the highest die.
    "Drop 2d2" defaults to "2d2 drop lowest"
    """

    priority_modifier = 5

    def _op(self, left: Number, right: Number) -> Number:
        return left

    def _set_probas(self, size, number, removed, lowest):
        self._probas = {}
        p_dict: P_FIELD = {
            tuple(comb): 1 / (size ** number)
            for comb in combinations(removed, size)
        }
        for combo in p_dict:
            proba = p_dict[combo]
            c: list[int] = list(combo)
            for _ in range(removed):
                if lowest:
                    i = np.argmin(c)
                else:
                    i = np.argmax(c)
                c = [C for j, C in enumerate(c) if j != i]
            s = sum(c)
            self._probas[s] = proba + self._probas.get(s, 0)

    def run(self, add_msg_discord: PUBLISHER_T = None) -> ExecutionResult:
        if not isinstance(self.right_child, SuperlativeNode):
            raise ValueError('Need to specify if we drop highest or lowest')
        if not isinstance(self.left_child, DiceNode):
            raise ValueError('Need to specify a dice roll to apply to this')

        lowest: bool = self.right_child.expression.startswith('lowest')
        how_many_to_take: int = self.right_child.run()[0]
        size: int = self.left_child.size
        how_many_to_roll: int = self.left_child.number

        # starting with all possible dice rolls
        if self._probas is None:
            self._set_probas(size, how_many_to_roll, how_many_to_take, lowest)

        # and now we choose a value
        r = random.random()
        sigma = 0
        for k in sorted(list(self._probas.keys())):
            sigma += self._probas[k]
            self.last_value = k
            if sigma > r:
                break
        return self.last_value, self._probas


class CompNode(Node, ABC, command='$'):

    priority_modifier = 8

    def _compare_to_multi_dice_roll(self, dice_left):
        dice: DiceNode = self.first_die_child()
        if dice_left:
            dice_side = self.left_child
            comp_to, comp_prob = self.right_child.run()
        else:
            dice_side = self.right_child
            comp_to, comp_prob = self.left_child.run()
        number = dice.number
        # import traceback
        # traceback.print_stack()
        # print("Repeat", number)
        dice.number = 1
        dice._probas = None

        rslt = 0
        self._probas = None

        for i in range(number):
            print("Iteration n°", i)
            result, probas = dice_side.run()
            if dice_left:
                rslt += self._op(result, comp_to)
            else:
                rslt += self._op(comp_to, result)
            proba = self.combine(probas, comp_prob)
            if self._probas is None:
                self._probas = proba
            self._probas = combine(self._probas, proba, lambda x, y: x + y)
        self.last_value = rslt

    def run(self, add_msg_discord: PUBLISHER_T = None) -> ExecutionResult:
        count_left_dice = self.left_child.count_dices_children()
        dice_left = count_left_dice == 1

        if (
                count_left_dice < 2
                # if there are more than two dice, do not lose time
                and
                count_left_dice + self.right_child.count_dices_children() == 1
        ):
            # only one die was rolled

            self._compare_to_multi_dice_roll(dice_left)
            return self.last_value, self._probas

        left_reslt, left_proba = self.left_child.run(add_msg_discord)
        right_reslt, right_proba = self.right_child.run(add_msg_discord)

        if self._probas:
            self._probas = self.combine(left_proba, right_proba)
        self.last_value = int(self._op(left_reslt, right_reslt))
        return self.last_value, self._probas


class GTNode(CompNode, command='>'):
    def _op(self, left: Number, right: Number) -> Number:
        return int(left > right)


class LTNode(CompNode, command='<'):
    def _op(self, left: Number, right: Number) -> Number:
        return int(left < right)


class GENode(CompNode, command='>='):
    def _op(self, left: Number, right: Number) -> Number:
        return int(left >= right)


class LENode(CompNode, command='<='):
    def _op(self, left: Number, right: Number) -> Number:
        return int(left <= right)


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
