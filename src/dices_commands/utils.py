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
import re


def ansi_skipping_len(s: str) -> int:
    """Because the length of an ANSI containing string is a bore...

    Args:
        s: (string): The string to be measured
    """
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


def clean_re(pattern: re.Pattern) -> str:
    # todo: choice cleaning with '|' detection
    return pattern.pattern.removeprefix('^').removesuffix('$')
