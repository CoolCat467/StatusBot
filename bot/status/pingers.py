#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Stolen and slightly modified from https://github.com/Dinnerbone/mcstatus

"Asynchronous and non-asynchronous Server Pinger classes."

# This version of mcstatus's pingers module
# has async and regular functions use the same parts with subfunctions

__all__ = ['ServerPinger', 'AsyncServerPinger']

import datetime
import json
from random import randint

from status.connection import Connection

class ServerPinger:
    "Server Pinger class, pings server with connection given."
    __slots__ = 'version', 'connection', 'host', 'port', 'ping_token'
    def __init__(
        self,
        connection,
        host: str = '',
        port: int = 0,
        version: int = 47,
        ping_token: int = None,
    ):
        "Requires connection object. Other values optional, but makes better."
        if ping_token is None:
            ping_token = randint(0, (1 << 63) - 1)
        self.version = version
        self.connection = connection
        self.host = host
        self.port = port
        self.ping_token = ping_token
    
    def handshake(self):
        "Preform handshake by writing buffer on self.connection."
        packet = Connection()
        packet.write_varint(0)
        packet.write_varint(self.version)
        packet.write_utf(self.host)
        packet.write_ushort(self.port)
        packet.write_varint(1)  # Intention to query status
        
        self.connection.write_buffer(packet)
    
    def _read_status_request(self):
        "Send request status packet to server."
        request = Connection()
        request.write_varint(0)  # Request status
        self.connection.write_buffer(request)
    
    @staticmethod
    def _read_status_process_response(response) -> dict:
        "Read response and return read value."
        if response.read_varint() != 0:
            raise IOError('Received invalid status response packet.')
        try:
            return json.loads(response.read_utf())
        except ValueError as ex:
            raise IOError('Received invalid JSON') from ex
        return {}
    
    def read_status(self) -> str:
        """Read status and return json response. Raises IOError."""
        self._read_status_request()
        
        response = self.connection.read_buffer()
        return self._read_status_process_response(response)
    
    def _test_ping_request(self) -> datetime.datetime:
        """Send test ping request. Return time sent at."""
        request = Connection()
        request.write_varint(1)  # Test ping
        request.write_long(self.ping_token)
        sent = datetime.datetime.now()
        self.connection.write_buffer(request)
        return sent
    
    def _test_ping_process_response(self, response, sent, received) -> float:
        "Read response, make sure token is good, return delta in ms. IOError on failure."
        if response.read_varint() != 1:
            raise IOError('Received invalid ping response packet.')
        received_token = response.read_long()
        if received_token != self.ping_token:
            msg = 'Received mangled ping response packet (expected token '
            raise IOError(
                mgs+f'{self.ping_token}, received {received_token})'
            )
        
        delta = received - sent
        # We have no trivial way of getting a time delta :(
        return (delta.days * 24 * 60 * 60 + delta.seconds) * 1000 + delta.microseconds / 1000
    
    def test_ping(self) -> float:
        "Send test ping, return delay (in miliseconds) delta from response."
        sent = self._test_ping_request()
        
        response = self.connection.read_buffer()
        received = datetime.datetime.now()
        return self._test_ping_process_response(response, sent, received)

class AsyncServerPinger(ServerPinger):
    "Asynchronous Server Pinger class."
    async def read_status(self) -> str:
        self._read_status_request()
        
        response = await self.connection.read_buffer()
        return self._read_status_process_response(response)
    
    async def test_ping(self) -> float:
        sent = self._test_ping_request()
        
        response = await self.connection.read_buffer()
        received = datetime.datetime.now()
        return self._test_ping_process_response(response, sent, received)
