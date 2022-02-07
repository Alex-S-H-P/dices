import curses
import curses.textpad as textpad
import time

import dices

DISPLAY, PLAY, INPUT = 0, 1, 2


def center(screen, string: str, cols: int, y: int, options: int = 1) -> None:
    len = dices.p_len(string)
    x = (cols - len) // 2
    screen.addstr(y, x, string)


def handle(command: str):
    command.lower().split()


def main(*args, **kwargs):
    def refresh(rows, cols):
        stdscr.clear()

        center(stdscr, "FIGHTING SIM", cols, 1, 1)
        stdscr.addstr(2, 0, "*" * cols, 1)
        stdscr.addstr(rows - rows_for_input, 0, "*" * cols, 1)
        box_window.resize(1, cols - 1)
        box_window.mvwin(rows - rows_for_input + 1, 1)

        curses.start_color()
        stdscr.refresh()

    # Clear screen
    instruction: str = ""
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    rows, cols = stdscr.getmaxyx()
    rows_for_title = 2
    rows_for_input = 3
    box_window = curses.newwin(1, cols, rows - rows_for_input + 1, 1)
    box = textpad.Textbox(box_window)
    mode: int = INPUT
    while True:
        rows, cols = stdscr.getmaxyx()
        refresh(rows, cols)
        ch = box_window.getch()
        if ch == curses.KEY_ENTER:
            instruction = box.gather()
            if instruction.lower() in dices.EXIT_INPUTS[1:]:
                break
            handle(instruction)
        else:
            box.do_command(ch)
        # refresh(rows, cols)
    stdscr.clear()
    y, x = stdscr.getmaxyx()
    center(stdscr, "GoodBye !", x, y // 2, 1)
    stdscr.refresh()
    time.sleep(0.3)
    return


if __name__ == '__main__':
    stdscr = curses.initscr()
    curses.start_color()
    curses.wrapper(main)
