"""General tools for updating."""

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

__title__ = "Update with Github"
__author__ = "CoolCat467"
__license__ = "Apache License 2.0"
__version__ = "0.1.7"
__ver_major__ = 0
__ver_minor__ = 1
__ver_patch__ = 7

import asyncio
import os
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from collections.abc import Iterable

TIMEOUT = 60


def get_address(user: str, repo: str, branch: str, path: str) -> str:
    """Get raw GitHub user content URL of a specific file."""
    return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}"


def is_new_ver_higher(current: Iterable[Any], newest: Iterable[Any]) -> bool:
    """Return True if current version older than new version."""
    return tuple(current) < tuple(newest)


def get_paths(jdict: dict[str, Any]) -> list[str]:
    """Read dictionary and figure out paths of files we want to update."""

    def read_dict(cdict: dict[str, Any]) -> list[str]:
        """Read a dictionary and return paths."""
        paths = []
        for path in cdict:
            nxt = cdict[path]
            # See next object.
            if isinstance(nxt, dict):
                # If dictionary, read and add our own path.
                add = read_dict(nxt)
                for file in add:
                    paths.append(os.path.join(path, file))
            else:
                # If it's a list or tuple, add all to our own paths joined.
                for file in nxt:
                    if isinstance(file, str):
                        paths.append(os.path.join(path, file))
        return paths

    return read_dict(jdict)


def make_dirpath_exist(filepath: str) -> None:
    """Ensure full folder structure to file path given exists.

    If not exists, creates it.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)


async def download_coroutine(
    url: str,
    timeout: int = TIMEOUT,
    headers: dict[str, Any] | None = None,
) -> bytes:
    """Return content bytes found at URL."""
    async with httpx.AsyncClient(http2=True, timeout=timeout) as client:
        # Go to the URL and get response
        response = await client.get(url, headers=headers)

        # Raise exceptions if errors happened
        response.raise_for_status()

        # Get response content
        request_result = response.read()

        # Close response
        await response.aclose()
    return request_result


async def get_file(
    repo: str,
    path: str,
    user: str,
    branch: str = "HEAD",
    timeout: int = TIMEOUT,
    **sessionkwargs: Any,
) -> bytes:
    """Return a file from a GitHub repository. Return data as bytes."""
    url = get_address(user, repo, branch, path)
    return await download_coroutine(url, timeout, **sessionkwargs)


async def update_file(
    basepath: str,  # pylint: disable=too-many-arguments
    repo: str,
    path: str,
    user: str,
    branch: str = "HEAD",
    timeout: int = TIMEOUT,
    **sessionkwargs: Any,
) -> bool:
    """Update file. Return False on exception, otherwise True."""
    url = get_address(user, repo, branch, path)
    savepath = os.path.abspath(os.path.join(basepath, *(path.split("/"))))
    try:
        with open(savepath, "wb") as sfile:
            sfile.write(
                await download_coroutine(url, timeout, **sessionkwargs),
            )
            sfile.close()
    except Exception:  # pylint: disable=W0703
        # We have to be able to catch all exceptions so we can return and
        # never have an exception in handling.
        return False
    return True


async def update_files(
    basepath: str,  # pylint: disable=too-many-arguments
    paths: tuple[str, ...],
    repo: str,
    user: str,
    branch: str = "HEAD",
    timeout: int = TIMEOUT,
    **sessionkwargs: Any,
) -> list[str]:
    """Update multiple files all from the same GitHub repository.

    Return list of paths.
    """
    urlbase = get_address(user, repo, branch, "")

    async def update_single(path: str) -> str:
        """Update a single file."""
        savepath = os.path.abspath(os.path.join(basepath, path))
        # Ensure folder for it exists too.
        make_dirpath_exist(savepath)
        url = urlbase + path
        with open(savepath, "wb") as sfile:
            sfile.write(
                await download_coroutine(url, timeout, **sessionkwargs),
            )
            sfile.close()
        return path

    coros = (update_single(path) for path in paths)
    return await asyncio.gather(*coros)


async def run_async(loop: asyncio.AbstractEventLoop) -> None:
    """Run asynchronously."""
    data = await get_file(
        "StatusBot",
        "version.txt",
        "CoolCat467",
        "HEAD",
        headers={
            "accept": "text/plain",
            # 'host': 'raw.githubusercontent.com'
        },
    )
    print(data.decode("utf-8"))
    data = await get_file(
        "StatusBot",
        "files.json",
        "CoolCat467",
        "HEAD",
        headers={
            "accept": "text/plain",
            # 'host': 'raw.githubusercontent.com'
        },
    )
    print(repr(data))
    import json

    paths = tuple(get_paths(json.loads(data.decode("utf-8"))))
    print(f"\n{paths = }")


def run() -> None:
    """Run test."""
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(run_async(loop))
    finally:
        loop.close()


if __name__ == "__main__":
    run()
