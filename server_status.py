#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# MC Server Status

# Programmed by CoolCat467
# Stolen almost all code from https://github.com/Dinnerbone/mcstatus

__title__ = 'MC Server Status'
__author__ = 'CoolCat467'
__version__ = '0.0.0'
__ver_major__ = 0
__ver_minor__ = 0
__ver_patch__ = 0

__all__ = ['try_x_times', 'Server']

from address_tools import lookup
from connection import *
from pingers import *
from functools import wraps

def try_x_times(times:int=3):
    '''Return a wraper that will attempt to run the function it wraps x times. If it fails the x th time, exception is allowed to go uncaught.'''
    def try_wraper(function):
        'Wrapper for given function to try times before exit.'
        @wraps(function)
        def try_function_wraper(*args, **kwargs):
            'Call a function with given arguments, raise exception on failure more than x times.'
            exception = None
            for attempt in range(times):
                try:
                    return function(*args, **kwargs)
                except Exception as e:
                    exception = e
            raise exception
        return try_function_wraper
    return try_wraper

class Server():
    'Server class talks to minecraft servers.'
    def __init__(self, host:str, port:int=25565):
        'Requires a host and a port.'
        self.host = host
        self.port = port
    
    @classmethod
    def lookup(cls, address:str):
        'Parses the given address and checks DNS records for an SRV record that points to the Minecraft server.'
        host, port = lookup(address, 25565, '_minecraft._tcp.{}', 'SRV')
        return cls(host, port)
    
    def ping(self, tries=3, **kwargs):
        'Return the latancy of the connection to the server in milisecconds.'
        connection = TCPSocketConnection((self.host, self.port))
        
        @try_x_times(tries)
        def ping_server():
            pinger = ServerPinger(connection, host=self.host, port=self.port, **kwargs)
            pinger.handshake()
            
            return pinger.test_ping()
        try:
            return ping_server()
        finally:
            connection.close()
    
    async def async_ping(self, tries=3, **kwargs):
        'Return the latancy of the connection to the server in milisecconds.'
        connection = TCPAsyncSocketConnection()
        await connection.connect((self.host, self.port))
        
        @try_x_times(tries)
        async def ping_server():
            pinger = AsyncServerPinger(connection, host=self.host, port=self.port, **kwargs)
            pinger.handshake()
            
            return await pinger.test_ping()
        try:
            return await ping_server()
        finally:
            connection.close()
    
    def status(self, tries=3, **kwargs):
        "Request the server's status and return the json from the response."
        connection = TCPSocketConnection((self.host, self.port))
        
        @try_x_times(tries)
        def get_status():
            pinger = ServerPinger(connection, host=self.host, port=self.port, **kwargs)
            pinger.handshake()
            
            result = pinger.read_status()
            latency = pinger.test_ping()
            return result, latency
        try:
            return get_status()
        finally:
            connection.close()
    
    async def async_status(self, tries=3, **kwargs):
        "Request the server's status and return the json from the response."
        connection = TCPAsyncSocketConnection()
        await connection.connect((self.host, self.port))
        
        @try_x_times(tries)
        async def get_status():
            pinger = AsyncServerPinger(connection, host=self.host, port=self.port, **kwargs)
            pinger.handshake()
            
            result = await pinger.read_status()
            latency = await pinger.test_ping()
            return result, latency
        try:
            return await get_status()
        finally:
            connection.close()
    pass

def run():
    cat = Server.lookup('mc.hypixel.net')
    import asyncio
    print(asyncio.run(cat.async_status()))
##    print(cat.status())
    del asyncio

if __name__ == '__main__':
    print('%s v%s\nProgrammed by %s.' % (__title__, __version__, __author__))
    run()
