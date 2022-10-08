#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# MC Server Status

"Supply Server class to ping a Java Minecraft Server."

# Programmed by CoolCat467
# Stolen almost all code from https://github.com/Dinnerbone/mcstatus

__title__ = 'MC Server Status'
__author__ = 'CoolCat467'
__version__ = '0.0.3'
__ver_major__ = 0
__ver_minor__ = 0
__ver_patch__ = 3

__all__ = ['try_x_times', 'Server']

from typing import Callable, Any, TypeVar, cast, Tuple

from functools import wraps as _wraps

from status.address_tools import lookup
from status.connection    import TCPAsyncSocketConnection
from status.pingers       import AsyncServerPinger

F = TypeVar('F', bound=Callable[..., Any])

def try_x_times(times: int=3) -> Callable[[F], F]:
    '''Return a wrapper that will attempt to run the function it wraps x times.
    If it fails the final time, exception is allowed to go uncaught.'''
    def try_wrapper(function: F) -> F:
        'Wrapper for given function to try times before exit.'
        @_wraps(function)
        def try_function_wrapper(*args: Any, **kwargs: Any) -> Any:
            'Call function with given arguments, re-raise exception if fails > x times.'
            for time in range(times):
                try:
                    return function(*args, **kwargs)
                except Exception:
                    if time == times-1:
                        raise
            return None
        return cast(F, try_function_wrapper)
    return try_wrapper

class Server:
    'Server class talks to minecraft servers.'
    __slots__ = ('host', 'port')
    def __init__(self, host: str, port: int=25565) -> None:
        'Requires a host and a port.'
        self.host = host
        self.port = port
    
    @classmethod
    def lookup(cls, address: str) -> 'Server':
        'Lookup Minecraft server from DNS records.'
        host, port = lookup(address, 25565, '_minecraft._tcp.{}', 'SRV')
        return cls(host, port)
    
    async def async_ping(self, tries: int=3) -> float:
        'Return the latency of the connection to the server in milliseconds.'
        connection = TCPAsyncSocketConnection()
        await connection.connect((self.host, self.port))
        
        @try_x_times(tries)
        async def ping_server() -> float:
            pinger = AsyncServerPinger(
                connection,
                host=self.host,
                port=self.port,

            )
            pinger.handshake()
            
            return await pinger.test_ping()
        try:
            return await ping_server()
        finally:
            connection.close()
    
    async def async_status(self, tries: int=3) -> Tuple[dict, float]:
        "Request the server's status and return the json from the response."
        connection = TCPAsyncSocketConnection()
        await connection.connect((self.host, self.port))
        
        @try_x_times(tries)
        async def get_status() -> Tuple[dict, float]:
            pinger = AsyncServerPinger(
                connection,
                host=self.host,
                port=self.port,
            )
            pinger.handshake()
            
            result = await pinger.read_status()
            latency = await pinger.test_ping()
            return result, latency
        try:
            return await get_status()
        finally:
            connection.close()

if __name__ == '__main__':
    print(f'{__title__} v{__version__}\nProgrammed by {__author__}.')
