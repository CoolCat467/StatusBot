#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Talk to github asyncronously

# Programmed by CoolCat467

__title__ = 'Update with Github'
__author__ = 'CoolCat467'
__version__ = '0.1.0'
__ver_major__ = 0
__ver_minor__ = 1
__ver_patch__ = 0

import os
import aiohttp
import async_timeout

from asyncio import gather

TIMEOUT = 10

def get_address(user, repo, branch, path):
    "Get raw github user content url of a specific file."
    return f'https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}'

async def download_coroutine(loop, url, timeout=TIMEOUT):
    "Return the sentance translated, asyncronously."
    # Make a session with our event loop and the magic headers that make it work right cause it's smart
    async with aiohttp.ClientSession(loop=loop) as session:
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

async def get_file(loop, repo, path, user=__author__, branch='HEAD', timeout=TIMEOUT):
    "Get a file from a github repository. Return data as text."
    url = get_address(user, repo, branch, path)
    return await download_coroutine(loop, url, timeout)

async def update_file(loop, basepath, repo, path, user=__author__, branch='HEAD', timeout=TIMEOUT):
    "Update file. Return False on exception, otherwise True."
    try:
        file = await get_file(loop, repo, path, user, branch, timeout)
        savepath = os.path.join(basepath, path)
        with open(savepath, 'w', encoding='utf-8') as sfile:
            sfile.write(file.decode('utf-8'))
            sfile.close()
        del file
    except:
        return False
    return True

async def update_files(loop, basepath, paths, repo, user=__author__, branch='HEAD', timeout=TIMEOUT) -> list:
    "Update multiple files all from the same github repository. Return list of paths."
    urlbase = get_address(user, repo, branch, '')
    async def update_single(path):
        "Update a single file."
        savepath = os.path.join(basepath, path)
        url = urlbase + path
        file = await download_coroutine(loop, url, timeout)
        with open(savepath, 'w', encoding='utf-8') as sfile:
            sfile.write(file.decode('utf-8'))
            sfile.close()
        del file
        return path
    coros = [update_single(path) for path in paths]
    return await gather(*coros, loop=loop)

def get_paths(jdict:dict) -> list:
    "Read dictionary and figure out paths of files we want to update."
    paths = []
    def read_dict(cdict):
        paths = []
        for path in cdict:
            nxt = cdict[path]
            if isinstance(nxt, dict):
                add = read_dict(nxt)
                for f in add:
                    paths.append(os.path.join(path, f))
            elif isinstance(nxt, (list, tuple)):
                for f in nxt:
                    paths.append(os.path.join(path, f))
        return paths
    return read_dict(jdict)

def run():
    import asyncio
    loop = asyncio.get_event_loop()
##    file = loop.run_until_complete(get_file(loop, 'StatusBot', 'version.txt', 'CoolCat467', 'HEAD', 5))
##    print([file.decode('utf-8').strip()])
##    #loop.close()
##    del asyncio
    basepath = os.path.expanduser('~/Desktop/StatusBot/bot')
    loop.run_until_complete(update_files(loop, basepath, ('version.txt', 'files.json'), 'StatusBot'))

if __name__ == '__main__':
    print('%s v%s\nProgrammed by %s.' % (__title__, __version__, __author__))
    run()
