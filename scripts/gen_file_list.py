#!/usr/bin/env python3
# Generate File Listing - Put into a folder, run, now you have a file listing

"""Generate File Listing."""

from __future__ import annotations

# Programmed by CoolCat467

__title__ = "Generate File List"
__author__ = "CoolCat467"
__version__ = "0.2.0"

import json
import os
from typing import Any, Container


def get_file_list(
    root: str,
    ignore_paths: Container | None = None,
) -> dict[str, dict | list[str]]:
    """Return file list dictionary."""
    if ignore_paths is None:
        ignore: Container = set()
    else:
        ignore = ignore_paths

    root_len = len(root) + len(os.path.sep)
    dirs: dict[str, Any] = {}

    for dirpath, _dirnames, filenames in os.walk(root):
        filenames = [
            f for f in filenames if f not in ignore and not f.startswith(".")
        ]
        if not filenames:
            continue
        entry = dirpath[root_len:]
        if entry.startswith("."):
            continue

        follow = entry.split(os.path.sep)

        if f"{follow[-1]}/" in ignore:
            continue

        if len(follow) > 1:
            if follow[0] not in dirs:
                dirs[follow[0]] = {}
            part = dirs[follow[0]]
            for link in follow[1:]:
                if link not in part:
                    part[link] = {}
                part = part[link]
            part[""] = filenames
        elif entry:
            dirs[entry] = {"": filenames}
        else:
            dirs[entry] = filenames
    return dirs


def read_gitignore() -> list[str]:
    """Read gitignore paths."""
    ignore = []
    if not os.path.exists(".gitignore"):
        return ignore
    with open(".gitignore", encoding="utf-8") as gitignore:
        for line in gitignore:
            line = line.strip()
            if line.startswith("#"):
                continue
            # TODO: Regex
            if "*" in line:
                continue
            ignore.append(line)
    return ignore


def run() -> None:
    """Generate file listing for update module."""
    root, this = os.path.split(__file__)
    ignore = set(read_gitignore())
    ignore.add(this)

    dirs = get_file_list(root, ignore)

    # print(dirs)

    with open(os.path.join(root, "files.json"), "w", encoding="utf-8") as fp:
        json.dump(dirs, fp, indent=2, sort_keys=True)
        fp.write("\n")
    print("\nData written.")


if __name__ == "__main__":
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.")
    run()
