#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# MC Server Status

"Supply Server class to ping a Java Minecraft Server."

# Programmed by CoolCat467
# Stolen almost all code from https://github.com/Dinnerbone/mcstatus

__title__ = 'MC Server Status'
__author__ = 'CoolCat467'
__version__ = '0.0.2'
__ver_major__ = 0
__ver_minor__ = 0
__ver_patch__ = 2

__all__ = ['try_x_times', 'Server']

from typing import Callable, Any, TypeVar, cast, Tuple, Dict

from functools import wraps as _wraps

from status.address_tools import lookup
from status.connection import TCPAsyncSocketConnection, TCPSocketConnection
from status.pingers import AsyncServerPinger

F = TypeVar('F', bound=Callable[..., Any])

def try_x_times(times: int=3) -> Callable[[F], F]:
    '''Return a wraper that will attempt to run the function it wraps x times.
    If it fails the x th time, exception is allowed to go uncaught.'''
    def try_wraper(function: F) -> F:
        'Wrapper for given function to try times before exit.'
        @_wraps(function)
        def try_function_wraper(*args: Any, **kwargs: Any) -> Any:
            'Call func with given args, reraise exception if fails > x times.'
            for time in range(times):
                try:
                    return function(*args, **kwargs)
                except Exception:
                    if time == times-1:
                        raise
            return None
        return cast(F, try_function_wraper)
    return try_wraper

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
    
    def ping(self, tries: int=3, **kwargs: Dict) -> float:
        'Return the latancy of the connection to the server in milisecconds.'
        connection = TCPSocketConnection((self.host, self.port))
        
        @try_x_times(tries)
        def ping_server() -> float:
            pinger = ServerPinger(connection, host=self.host, port=self.port, **kwargs)# type: ignore
            pinger.handshake()
            
            return pinger.test_ping()
        try:
            return ping_server()
        finally:
            connection.close()
    
    async def async_ping(self, tries: int=3, **kwargs: Dict) -> float:
        'Return the latancy of the connection to the server in milisecconds.'
        connection = TCPAsyncSocketConnection()
        await connection.connect((self.host, self.port))
        
        @try_x_times(tries)
        async def ping_server() -> float:
            pinger = AsyncServerPinger(connection, host=self.host, port=self.port, **kwargs)# type: ignore
            pinger.handshake()
            
            return await pinger.test_ping()
        try:
            return await ping_server()
        finally:
            connection.close()
    
    def status(self, tries: int=3, **kwargs: Dict) -> Tuple[Dict, float]:
        "Request the server's status and return the json from the response."
        connection = TCPSocketConnection((self.host, self.port))
        
        @try_x_times(tries)
        def get_status() -> Tuple[Dict, float]:
            pinger = ServerPinger(connection, host=self.host, port=self.port, **kwargs)# type: ignore
            pinger.handshake()
            
            result = pinger.read_status()
            latency = pinger.test_ping()
            return result, latency
        try:
            return get_status()
        finally:
            connection.close()
    
    async def async_status(self, tries: int=3, **kwargs: Dict) -> Tuple[dict, float]:
        "Request the server's status and return the json from the response."
        connection = TCPAsyncSocketConnection()
        await connection.connect((self.host, self.port))
        
        @try_x_times(tries)
        async def get_status() -> Tuple[dict, float]:
            pinger = AsyncServerPinger(connection, host=self.host, port=self.port, **kwargs)# type: ignore
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
