#!/usr/bin/env python3
# Force update bot

"Force Update Bot."

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

__title__ = "Force update"
__author__ = "CoolCat467"
__license__ = "Apache License 2.0"
__version__ = "0.0.2"
__ver_major__ = 0
__ver_minor__ = 0
__ver_patch__ = 2

import asyncio
import json
from os.path import abspath, split
from typing import Final

import update

ROOTDIR: Final = split(abspath(__file__))[0]


async def get_github_file(path: str, timeout: int = 10) -> str:
    "Return text from GitHub file in this project decoded as utf-8."
    file = await update.get_file(
        "StatusBot",
        path,
        __author__,
        "HEAD",
        timeout,
    )
    value = file.decode("utf-8")
    assert isinstance(value, str)
    return value


async def getonlinevers() -> tuple[int, ...]:
    "Return online version as tuple."
    # Get GitHub version string
    version = await get_github_file("version.txt")
    # Send message about it.
    print(f"Online version: {version}")
    # Make it tuple and return it
    return tuple(map(int, version.strip().split(".")))


async def update_files(timeout: int = 20) -> None:
    "Perform update from GitHub."
    # If we need update, get file list.
    print("Retrieving file list...")
    try:
        response = await get_github_file("files.json")
        print(response)
        paths = tuple(update.get_paths(json.loads(response)))
    except Exception:
        # On failure, tell them we can't read file.
        print("Could not read file list. Aborting update.")
        raise
    # Get max amount of time this could take.
    # Tell user number of files we are updating.
    print(f"{len(paths)} files will now be updated.\n")
    # Update said files.
    rootdir = split(ROOTDIR)[0]
    print("\n".join(paths))
    await update.update_files(
        rootdir,
        paths,
        "StatusBot",
        __author__,
        "HEAD",
        timeout,
    )
    print("\nAll files in file list updated.")


def run() -> None:
    "Perform update."
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(update_files())
    finally:
        # cancel all lingering tasks
        loop.close()


if __name__ == "__main__":
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
    run()
