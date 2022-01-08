#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Force update bot

"""Force Update Bot"""

# Programmed by CoolCat467

__title__ = 'Force update'
__author__ = 'CoolCat467'
__version__ = '0.0.0'
__ver_major__ = 0
__ver_minor__ = 0
__ver_patch__ = 0

import os
import asyncio
import json
import update

ROOTDIR = os.path.split(os.path.abspath(__file__))[0]

async def get_github_file(path:str, timeout:int=10) -> str:
    "Return text from github file in this project decoded as utf-8"
    file = await update.get_file('StatusBot', path, __author__, 'master', timeout)
    return file.decode('utf-8')

async def getonlinevers() -> tuple:
    "Get online version, tell user in message.channel, and return said version as tuple."
    # Get github version string
    version = await get_github_file('version.txt')
    # Send message about it.
    print(f'Online version: {version}')
    # Make it tuple and return it
    return tuple(map(int, version.strip().split('.')))

async def update_files(timeout:int=20) -> None:
    "Preform update from github."
    # If we need update, get file list.
    print('Retrieving file list...')
    try:
        response = await get_github_file('files.json')
        paths = tuple(update.get_paths(json.loads(response)))
    except Exception:
        # On failure, tell them we can't read file.
        print('Could not read file list. Aborting update.')
        return
    # Get max amount of time this could take.
    maxtime = timeout*len(paths)
    # Tell user number of files we are updating.
    print(f'{len(paths)} files will now be updated. ')
    # Update said files.
    rootdir = os.path.split(ROOTDIR)[0]
    await update.update_files(rootdir, paths, 'StatusBot', __author__, 'master', timeout)
    print('Done.')

def run():
    "Preform update."
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(update_files())
    finally:
        # cancel all lingering tasks
        loop.close()




if __name__ == '__main__':
    print(f'{__title__} v{__version__}\nProgrammed by {__author__}.')
    run()
