import curses
import dices


def main(screen, *args, **kwargs):
    # Clear screen
    screen.clear()

    # This raises ZeroDivisionError when i == 10.
    for i in range(1, 11):
        v = i - 10
        print(i, v)
        screen.addstr(i, 0, '10 divided by {} is {}'.format(v, 10 / v))

    screen.refresh()
    screen.getkey()


if __name__ == '__main__':
    stdscr = curses.initscr()
    curses.wrapper(main, stdscr)
