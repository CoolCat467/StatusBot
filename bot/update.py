#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# General tools for updating

"General tools for updating."

# Programmed by CoolCat467

__title__ = 'Update with Github'
__author__ = 'CoolCat467'
__version__ = '0.1.2'
__ver_major__ = 0
__ver_minor__ = 1
__ver_patch__ = 2

from os import path
import aiohttp
import async_timeout

from asyncio import gather

TIMEOUT = 10

def get_address(user:str, repo:str, branch:str, path:str) -> str:
    "Get raw github user content url of a specific file."
    return f'https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}'

def is_new_ver_higher(current:tuple, new:tuple) -> bool:
    "Return True if current version older than new version."
    assert len(current) == len(new), 'Version lengths do not match!'
    for old, new in zip(current, new):
        if old < new:
            return True
        elif old == new:
            continue
        return False
    return False

def get_paths(jdict:dict) -> list:
    "Read dictionary and figure out paths of files we want to update."
    paths = []
    def read_dict(cdict:dict) -> list:
        "Read a dictonary and return paths."
        paths = []
        for path in cdict:
            nxt = cdict[path]
            # See next object.
            if isinstance(nxt, dict):
                # If dictionary, read and add our own path.
                add = read_dict(nxt)
                for f in add:
                    paths.append(path.join(path, f))
            elif isinstance(nxt, (list, tuple)):
                # If it's a list or tuple, add all to our own paths joined.
                for f in nxt:
                    if isinstance(f, str):
                        paths.append(path.join(path, f))
        return paths
    return read_dict(jdict)

async def download_coroutine(url:str, timeout:int=TIMEOUT, **sessionkwargs) -> bytes:
    "Return content bytes found at url."
    # Make a session with our event loop and the magic headers that make it work right cause it's smart
    async with aiohttp.ClientSession(**sessionkwargs) as session:
        # Make sure we have a timeout, so that in the event of network failures or something code doesn't get stuck
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

async def get_file(repo:str, path:str, user:str, branch:str='HEAD', timeout:int=TIMEOUT, **sessionkwargs) -> bytes:
    "Get a file from a github repository. Return data as bytes."
    url = get_address(user, repo, branch, path)
    return await download_coroutine(url, timeout, **sessionkwargs)

async def update_file(basepath:str, repo:str, path:str, user:str, branch:str='HEAD', timeout:int=TIMEOUT, **sessionkwargs) -> bool:
    "Update file. Return False on exception, otherwise True."
    try:
        filedata = await get_file(repo, path, user, branch, timeout, **sessionkwargs)
        savepath = path.join(basepath, path)
        with open(savepath, 'wb') as sfile:
            sfile.write(filedata)
            sfile.close()
        del file
    except:
        return False
    return True

async def update_files(basepath:str, paths:tuple, repo:str, user:str, branch:str='HEAD', timeout:int=TIMEOUT, **sessionkwargs) -> list:
    "Update multiple files all from the same github repository. Return list of paths."
    urlbase = get_address(user, repo, branch, '')
    async def update_single(path):
        "Update a single file."
        savepath = path.abspath(path.join(basepath, path))
        url = urlbase + path
        with open(savepath, 'wb') as sfile:
            sfile.write(await download_coroutine(url, timeout, **sessionkwargs))
            sfile.close()
        del file
        return path
    coros = (update_single(path) for path in paths)
    return await gather(*coros)

def run():
    import asyncio
    loop = asyncio.get_event_loop()
    file = loop.run_until_complete(get_file('StatusBot', 'version.txt', 'CoolCat467', 'HEAD', 5))
    print(file.decode('utf-8').strip())
    del asyncio
    
if __name__ == '__main__':
    print('%s v%s\nProgrammed by %s.' % (__title__, __version__, __author__))
    run()
