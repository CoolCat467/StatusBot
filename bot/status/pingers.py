#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Stolen and slightly modified from https://github.com/Dinnerbone/mcstatus

"Asynchronous and non-asynchronous Server Pinger classes."

import datetime
import json
from random import randint
import io
from typing import Any, Dict, Tuple

##from ctypes import c_int32  as signed_int32

from status.connection import Connection, TCPAsyncSocketConnection


def decode_optimized(string: str) -> Connection:
    "Decode buffer from string"
    text = io.StringIO(string)

    def read() -> int:
        result = text.read(1)
        if not result:
            return 0
        return ord(result)

    size = read() | (read() << 15)

    buffer = Connection()
    value = 0
    bits = 0
    for _ in range(len(string) - 2):
        while bits >= 8:
            buffer.receive((value & 0xff).to_bytes())
            value >>= 8
            bits -= 8
        value |= (read() & 0x7FFF) << bits
        bits += 15

    while buffer.remaining() < size:
        buffer.receive((value & 0xff).to_bytes())
        value >>= 8
        bits -= 8
    return buffer


VERSION_FLAG_IGNORESERVERONLY = 0b1
##IGNORESERVERONLY = 'OHNOES\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31'
IGNORESERVERONLY = '<not required for client>'


def process_response(data: Dict[str, Any]) -> Dict[str, Any]:
    "Decode encoded forgeData if present"
    if not 'forgeData' in data:
        return data
    forge = data['forgeData']
    if not 'd' in forge:
        return data

    buffer = decode_optimized(forge['d'])

    channels: Dict[Tuple[str, str], Tuple[str, bool]] = {}
##    channels: Dict[str, Tuple[str, bool]] = {}
    mods: Dict[str, str] = {}

    try:
        truncated = buffer.read_bool()
        mod_size = buffer.read_ushort()
        for _ in range(mod_size):
            channel_version_flags = buffer.read_varint()

##            channel_size = signed_int32(channel_version_flags).value >> 1
            channel_size = channel_version_flags >> 1
            is_server = channel_version_flags & VERSION_FLAG_IGNORESERVERONLY != 0
            mod_id = buffer.read_utf()

            mod_version = IGNORESERVERONLY
            if not is_server:
                mod_version = buffer.read_utf()

            for _ in range(channel_size):
                name = buffer.read_utf()
                version = buffer.read_utf()
                client_required = buffer.read_bool()
##                channels[f'{mod_id}:{name}'] = (version, client_required)
                channels[(mod_id, name)] = (version, client_required)

            mods[mod_id] = mod_version

        non_mod_channel_size = buffer.read_varint()
        for _ in range(non_mod_channel_size):
            name = tuple(buffer.read_utf().split(':', 1))
##            name = buffer.read_utf()
            version = buffer.read_utf()
            client_required = buffer.read_bool()
##            channels[name] = (version, client_required)
            channels[name] = (version, client_required)
    except Exception as ex:
        if not truncated:
            print(f'Encountered {ex!r} decoding forge response, silently ignoring')
        # Semi-expect errors if truncated

    new_forge = {}
    for k, v in forge.items():
        if k == 'd':
            continue
        new_forge[k] = v
    new_forge['truncated'] = truncated
    new_forge['mods'] = mods
    new_forge['channels'] = channels
    data['forgeData'] = new_forge
    return data


class AsyncServerPinger:
    "Asynchronous Server Pinger class, pings server with connection given."
    __slots__ = 'version', 'connection', 'host', 'port', 'ping_token'
    def __init__(
        self,
        connection: TCPAsyncSocketConnection,
        host: str = '',
        port: int = 0,
        version: int = 47,
        ping_token: int = None,
    ) -> None:
        "Requires connection object. Other values optional, but makes better."
        if ping_token is None:
            ping_token = randint(0, (1 << 63) - 1)
        self.version = version
        self.connection = connection
        self.host = host
        self.port = port
        self.ping_token = ping_token

    def handshake(self) -> None:
        "Preform handshake by writing buffer on self.connection."
        packet = Connection()
        packet.write_varint(0)
        packet.write_varint(self.version)
        packet.write_utf(self.host)
        packet.write_ushort(self.port)
        packet.write_varint(1)  # Intention to query status

        self.connection.write_buffer(packet)

    def _read_status_request(self) -> None:
        "Send request status packet to server."
        request = Connection()
        request.write_varint(0)  # Request status
        self.connection.write_buffer(request)

    @staticmethod
    def _read_status_process_response(response: Connection) -> dict:
        "Read response and return read value."
        if response.read_varint() != 0:
            raise IOError('Received invalid status response packet.')
        try:
            return process_response(json.loads(response.read_utf()))
        except ValueError as ex:
            raise IOError('Received invalid JSON') from ex
        return {}

    async def read_status(self) -> dict:
        "Read status and return json response. Raises IOError."
        self._read_status_request()

        response = await self.connection.read_buffer()
        return self._read_status_process_response(response)

    def _test_ping_request(self) -> datetime.datetime:
        "Send test ping request. Return time sent at."
        request = Connection()
        request.write_varint(1)  # Test ping
        request.write_long(self.ping_token)
        sent = datetime.datetime.now()
        self.connection.write_buffer(request)
        return sent

    def _test_ping_process_response(self,
                                    response: Connection,
                                    sent: datetime.datetime,
                                    received: datetime.datetime
                                    ) -> float:
        "Read response, make sure token is good, return delta in ms. IOError on failure."
        if response.read_varint() != 1:
            raise IOError('Received invalid ping response packet.')
        received_token = response.read_long()
        if received_token != self.ping_token:
            msg = 'Received mangled ping response packet (expected token '
            raise IOError(
                msg+f'{self.ping_token}, received {received_token})'
            )

        delta = received - sent
        # We have no trivial way of getting a time delta :(
        return (delta.days * 24 * 60 * 60 + delta.seconds) * 1000 + delta.microseconds / 1000

    async def test_ping(self) -> float:
        "Send test ping, return delay (in milliseconds) delta from response."
        sent = self._test_ping_request()

        response = await self.connection.read_buffer()
        received = datetime.datetime.now()
        return self._test_ping_process_response(response, sent, received)
