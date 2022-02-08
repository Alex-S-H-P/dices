"""The head of the Fighting sim of the whole repository."""

import curses
import curses.textpad as textpad
import time
import typing

import dices
import fight_back
import fight_funcs

dices.verbose = False


def center(screen, string: str, cols: int, y: int, options: int = 1) -> None:
    len = dices.p_len(string)
    x = (cols - len) // 2
    screen.addstr(y, x, string, options)


def find_function(instruction: list[str]) -> typing.Optional[fight_funcs.Operation]:
    aligned_words = 0
    function_name = instruction[0]
    while True:
        aligned_words += 1
        if function_name in fight_funcs.func_map:
            for index in range(1, aligned_words):
                instruction.pop(index)
                instruction[0] = function_name
            return fight_funcs.func_map[function_name]
        else:
            if len(instruction) > aligned_words:
                if not instruction[aligned_words].isnumeric():
                    function_name += "_" + instruction[aligned_words]
                else:
                    return None
            else:
                return None


def handle(command: str, display: fight_funcs.Display) -> str:
    instruction = dices.segment(command.lower())
    method = find_function(instruction)
    if method is not None:
        try:
            return str(method(instruction, display))
        except Exception as e:
            raise e
            return f"ERR : {e}"
    else:
        return f"ERR : UNKNOWN COMMAND '{instruction[0]}'"


def main(*args, **kwargs):
    def _update_head(c: int):
        head.resize(2, c)
        head.clear()
        center(head, "FIGHT SIM", c, 0, CYAN)
        head.addstr(1, 0, "*" * (c - 1), YELLOW)

    def _update_body(r: int, c: int):
        body.resize(r - 4, c)
        max_lines = r - 4
        body.mvwin(2, 0)
        body.clear()
        lines_written = 0

        for fighter in display.fight:
            arrow = f"{fighter.initiative}❯"
            body.addstr(lines_written, 0, arrow, CYAN)
            for i, line in enumerate(fighter.lines()):
                body.addstr(lines_written, len(arrow) if i == 0 else len(arrow) + 2,  # coordinates
                            line,  # text
                            ACTIVE_FIGHTER if fighter.active else INACTIVE_FIGHTER)  # style
                lines_written += 1
                if lines_written == max_lines:
                    break
            if lines_written == max_lines:
                break

    def _update_sep(r: int, c: int):
        sep.resize(1, c)
        sep.mvwin(r - 2, 0)
        sep.clear()
        sep.addstr(0, 0, "*" * (c - 1), YELLOW)

    def _update_tail(r: int, c: int):
        tail.resize(1, c)
        tail.mvwin(r - 1, 0)

    def update(old_r, old_c):
        r, c = stdscr.getmaxyx()
        if c != old_c or old_r != r:
            stdscr.clear()
            _update_head(c)
            _update_body(r, c)
            _update_sep(r, c)
            _update_tail(r, c)
            # body.addstr(f"updated_sizes !, {oldr}->{r}, {oldc}->{c}")
        head.refresh()
        body.refresh()
        sep.refresh()
        tail.refresh()

        return r, c

    rows, cols = 5, 12
    head = curses.newwin(2, cols, 0, 0)
    body = curses.newwin(rows - 4, cols, 2, 0)
    sep = curses.newwin(1, cols, rows - 2, 0)
    tail = curses.newwin(1, cols, rows - 1, 0)
    input_box = curses.textpad.Textbox(tail)
    display = fight_funcs.Display(fight)
    sep_is_used_as_display = False
    while True:
        rows, cols = update(rows, cols)
        ch = tail.getch()
        # we clean the sep if needed
        if sep_is_used_as_display:
            _update_sep(rows, cols)
            sep_is_used_as_display = False
            sep.refresh()
        # we handle the character we have received !
        if ch == 10 or ch == curses.KEY_ENTER:
            inp = input_box.gather().lower()
            if inp in dices.EXIT_INPUTS:
                break
            for _ in inp:
                input_box.do_command(curses.KEY_BACKSPACE)
            answer = handle(inp, display)
            sep.addstr(0, 0, answer, RED if answer.startswith("ERR") else GREEN)
            sep_is_used_as_display = True
            _update_body(rows, cols)
            body.refresh()
        else:
            input_box.do_command(ch)
        tail.refresh()
    stdscr.clear()
    x, y = stdscr.getmaxyx()
    center(stdscr, "Good bye !", y, x // 2, GREEN)

    stdscr.getch()
    return


if __name__ == '__main__':
    fight = fight_back.Fight()
    stdscr = curses.initscr()
    stdscr.keypad(True)
    curses.cbreak()
    curses.start_color()
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(6, curses.COLOR_CYAN, -1)
    curses.init_pair(16, -1, curses.COLOR_CYAN)
    curses.init_pair(0, -1, -1)

    INACTIVE_FIGHTER = DEFAULT = curses.color_pair(0)
    RED = curses.color_pair(1)
    GREEN = curses.color_pair(2)
    YELLOW = curses.color_pair(3)
    CYAN = curses.color_pair(6)
    ACTIVE_FIGHTER = curses.color_pair(16)

    curses.wrapper(main)
