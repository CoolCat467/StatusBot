#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Talk to github

# Programmed by CoolCat467

__title__ = 'Update with Github'
__author__ = 'CoolCat467'
__version__ = '0.0.0'
__ver_major__ = 0
__ver_minor__ = 0
__ver_patch__ = 0

import aiohttp
import async_timeout

TIMEOUT = 30

def get_address(user, repo, branch, path):
    """Get raw github user content url of a specific file."""
    return f'https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}'

async def download_coroutine(loop, url):
    """Return the sentance translated, asyncronously."""
    # Make a session with our event loop and the magic headers that make it work right cause it's smart
    async with aiohttp.ClientSession(loop=loop) as session:
        # Make sure we have a timeout, so that in the event of network failures or something code doesn't get stuck
        async with async_timeout.timeout(TIMEOUT):
            # Go to the url and get response
            async with session.get(url) as response:
                # Wait for our response
                request_result = await response.content.read()
                # Close response socket/file descriptor
                response.close()
        # Close session
        await session.close()
    return request_result

async def get_file(loop, repo, path, user=__author__, branch='master'):
    """Get a file from a github repository. Return data as text."""
    url = get_address(user, repo, branch, path)
    return await download_coroutine(loop, url)

def run():
    pass

if __name__ == '__main__':
    print('%s v%s\nProgrammed by %s.' % (__title__, __version__, __author__))
    run()
