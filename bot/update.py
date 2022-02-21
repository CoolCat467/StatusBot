#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# General tools for updating

"General tools for updating."

# Programmed by CoolCat467

__title__ = 'Update with Github'
__author__ = 'CoolCat467'
__version__ = '0.1.6'
__ver_major__ = 0
__ver_minor__ = 1
__ver_patch__ = 6

import os
from asyncio import gather

import aiohttp
import async_timeout

TIMEOUT = 10

def get_address(user: str, repo: str, branch: str, path: str) -> str:
    "Get raw github user content url of a specific file."
    return f'https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}'

def is_new_ver_higher(current: tuple, newest: tuple) -> bool:
    "Return True if current version older than new version."
    # Turns out, tuples have built in comparison support.
    # Exactly what we need lol. And it's better.
    return tuple(current) < tuple(newest)
##    for old, new in zip(current, newest):
##        if old < new:
##            return True
##        if old == new:
##            continue
##        return False
##    return False

def get_paths(jdict: dict) -> list:
    "Read dictionary and figure out paths of files we want to update."
    def read_dict(cdict: dict) -> list:
        "Read a dictonary and return paths."
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
    "Ensure full folder structure to filepath given exists. If not exists, creates it."
    # Folder we want to ensure exists.
    folder = os.path.dirname(filepath)
    # If folder not exist
    if not os.path.exists(folder):
        # Ensure above folder exists
        make_dirpath_exist(folder)
        # Make folder
        os.mkdir(folder)

async def download_coroutine(url: str, timeout: int=TIMEOUT, **sessionkwargs) -> bytes:
    "Return content bytes found at url."
    # Make a session with our event loop
    async with aiohttp.ClientSession(**sessionkwargs) as session:
        # Make sure we have a timeout, so that in the event of
        # network failures or something code doesn't get stuck
        async with async_timeout.timeout(timeout):
            # Go to the url and get response
            async with session.get(url) as response:
                # Wait for our response
                request_result = await response.content.read()
                # Close response socket/file descriptor
                response.close()
        # Close session
        await session.close()
    return request_result

async def get_file(repo: str, path: str, user: str, branch: str='HEAD',
                   timeout: int=TIMEOUT, **sessionkwargs) -> bytes:
    "Get a file from a github repository. Return data as bytes."
    url = get_address(user, repo, branch, path)
    return await download_coroutine(url, timeout, **sessionkwargs)

async def update_file(basepath: str, repo: str, path: str, user: str,# pylint: disable=R0913
                      branch: str='HEAD', timeout: int=TIMEOUT,
                      **sessionkwargs) -> bool:
    "Update file. Return False on exception, otherwise True."
    url = get_address(user, repo, branch, path)
    savepath = os.path.abspath(os.path.join(basepath, path))
    try:
        with open(savepath, 'wb') as sfile:
            sfile.write(await download_coroutine(url, timeout, **sessionkwargs))
            sfile.close()
    except Exception: # pylint: disable=W0703
        # We have to be able to catch all exceptions so we can return and
        # never have an exception in handling.
        return False
    return True

async def update_files(basepath: str, paths: tuple,# pylint: disable=R0913
                       repo: str, user: str, branch: str='HEAD',
                       timeout: int=TIMEOUT, **sessionkwargs) -> list:
    "Update multiple files all from the same github repository. Return list of paths."
    urlbase = get_address(user, repo, branch, '')
    async def update_single(path):
        "Update a single file."
        savepath = os.path.abspath(os.path.join(basepath, path))
        # Ensure folder for it exists too.
        make_dirpath_exist(savepath)
        url = urlbase + path
        with open(savepath, 'wb') as sfile:
            sfile.write(await download_coroutine(url, timeout, **sessionkwargs))
            sfile.close()
        return path
    coros = (update_single(path) for path in paths)
    return await gather(*coros)
