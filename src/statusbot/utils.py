"""Utilities."""

# Programmed by CoolCat467

# Copyright 2023 CoolCat467
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from __future__ import annotations

__title__ = "Utilities"
__author__ = "CoolCat467"
__license__ = "Apache License 2.0"
__version__ = "0.0.0"

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def split_time(seconds: int) -> list[int]:
    """Split time."""
    seconds = int(seconds)

    def mod_time(sec: int, num: int) -> tuple[int, int]:
        """Return number of times sec divides equally by number, then remainder."""
        smod = sec % num
        return int((sec - smod) // num), smod

    # pylint: disable=wrong-spelling-in-comment
    # values = (1, 60, 60, 24, 7, 365/12/7, 12, 10, 10, 10, 1000, 10, 10, 5)
    # mults = {0:values[0]}
    # for i in range(len(values)):
    # mults[i+1] = round(mults[i] * values[i])
    # divs = list(reversed(mults.values()))[:-1]
    divs = (
        15768000000000000,
        3153600000000000,
        315360000000000,
        31536000000000,
        31536000000,
        3153600000,
        315360000,
        31536000,
        2628000,
        604800,
        86400,
        3600,
        60,
        1,
    )
    ret = []
    for num in divs:
        edivs, seconds = mod_time(seconds, num)
        ret.append(edivs)
    return ret


def combine_end(data: Iterable[str], final: str = "and") -> str:
    """Join values of text, and have final with the last one properly."""
    data = list(map(str, data))
    if len(data) >= 2:
        data[-1] = f"{final} {data[-1]}"
    if len(data) > 2:
        return ", ".join(data)
    return " ".join(data)


def format_time(seconds: int, single_title_allowed: bool = False) -> str:
    """Return time using the output of split_time."""
    times = (
        "eons",
        "eras",
        "epochs",
        "ages",
        "millenniums",
        "centuries",
        "decades",
        "years",
        "months",
        "weeks",
        "days",
        "hours",
        "minutes",
        "seconds",
    )
    single = [i[:-1] for i in times]
    single[5] = "century"
    zip_idx_values = [(i, v) for i, v in enumerate(split_time(seconds)) if v]
    if single_title_allowed and len(zip_idx_values) == 1:
        index, value = zip_idx_values[0]
        if value == 1:
            return f"a {single[index]}"
    data = []
    for index, value in zip_idx_values:
        title = single[index] if abs(value) < 2 else times[index]
        data.append(f"{value} {title}")
    return combine_end(data)


if __name__ == "__main__":
    print(f"{__title__}\nProgrammed by {__author__}.\n")
