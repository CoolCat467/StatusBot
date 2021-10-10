#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Stolen and slightly modified from https://github.com/Dinnerbone/mcstatus

"TCP and UDP Connections, both asynchronous and not."

# This version of mcstatus's connection module
# has support for varlongs and has general text reformatting
# and spaceing changes. Slight changes to Asyncronous TCP and UDP
# closing as well.

__all__ = ['BaseConnection', 'Connection', 'AsyncReadConnection',
           'TCPSocketConnection', 'UDPSocketConnection',
           'TCPAsyncSocketConnection', 'UDPAsyncSocketConnection']

from abc import abstractmethod, ABC
import socket
import struct
import asyncio

from ctypes import c_uint32 as unsigned_int32
from ctypes import c_int32 as signed_int32
from ctypes import c_uint64 as unsigned_int64
from ctypes import c_int64 as signed_int64

import asyncio_dgram

from status.address_tools import ip_type

class BaseConnection(ABC):
    "Base connection class."
    @abstractmethod
    def read(self, length: int) -> bytearray:
        "Read length bytes from self, return a bytearray."
        ...
    
    @abstractmethod
    def write(self, data: bytes) -> None:
        "Write data to self."
        ...
    
    def __repr__(self) -> str:
        "Return representation of self."
        return f'{self.__class__.__name__} Object'
    
    def flush(self) -> None:
        "Raise TypeError, unsupported."
        raise TypeError(f'{self.__class__.__name__} does not support flush()')
    
    def receive(self, data: None) -> None:
        "Raise TypeError, unsupported."
        raise TypeError(f'{self.__class__.__name__} does not support receive()')
    
    def remaining(self) -> None:
        "Raise TypeError, unsupported."
        raise TypeError(f'{self.__class__.__name__} does not support remaining()')
    
    @staticmethod
    def _unpack(format_, data: bytes) -> str:
        "Unpack data as bytes with format in big-enidian."
        return struct.unpack('>' + format_, bytes(data))[0]
    
    @staticmethod
    def _pack(format_, data: str) -> bytes:
        "Pack data in with format in big-endian mode."
        return struct.pack('>' + format_, data)
    
    def read_varint(self) -> int:
        """Read varint from self and return it.
        Max: 2 ** 31 - 1, Min: -(2 ** 31)
        Raises IOError when varint recieved is too big."""
        result = 0
        for i in range(5):
            part = self.read(1)[0]
            result |= (part & 0x7F) << (7 * i)
            if not part & 0x80:
                return signed_int32(result).value
        raise IOError('Recieved varint is too big!')
    
    def write_varint(self, value: int) -> None:
        """Write varint with value value to self.
        Max: 2 ** 31 - 1, Min: -(2 ** 31).
        Raises ValueError if varint is too big."""
        remaining = unsigned_int32(value).value
        for _ in range(5):
            if not remaining & -0x80:#remaining & ~0x7F == 0:
                self.write(struct.pack('!B', remaining))
                if value > 2 ** 31 - 1 or value < -(2 ** 31):
                    break
                return
            self.write(struct.pack('!B', remaining & 0x7F | 0x80))
            remaining >>= 7
        raise ValueError(f'The value "{value}" is too big to send in a varint')
    
    def read_varlong(self) -> int:
        """Read varlong from self and return it.
        Max: 2 ** 63 - 1, Min: -(2 ** 63).
        Raises IOError when varint recieved is too big."""
        result = 0
        for i in range(10):
            part = self.read(1)[0]
            result |= (part & 0x7F) << (7 * i)
            if not part & 0x80:
                return signed_int64(result).value
        raise IOError('Recieved varlong is too big!')
    
    def write_varlong(self, value: int) -> None:
        """Write varlong with value value to self.
        Max: 2 ** 63 - 1, Min: -(2 ** 63).
        Raises ValueError if varint is too big."""
        remaining = unsigned_int64(value).value
        for _ in range(10):
            if not remaining & -0x80:#remaining & ~0x7F == 0:
                self.write(struct.pack('!B', remaining))
                if value > 2 ** 63 - 1 or value < -(2 ** 31):
                    break
                return
            self.write(struct.pack('!B', remaining & 0x7F | 0x80))
            remaining >>= 7
        raise ValueError(f'The value "{value}" is too big to send in a varlong')
    
    def read_utf(self) -> str:
        "Read up to 32767 bytes by reading a varint, then decode bytes as utf8."
        length = self.read_varint()
        return self.read(length).decode('utf8')
    
    def write_utf(self, value: str) -> None:
        "Write varint of length of value up to 32767 bytes, then write value encoded with utf8."
        self.write_varint(len(value))
        self.write(bytearray(value, 'utf8'))
    
    def read_ascii(self) -> str:
        "Read self until last value is not zero, then return that decoded with ISO-8859-1"
        result = bytearray()
        while len(result) == 0 or result[-1] != 0:
            result.extend(self.read(1))
        return result[:-1].decode('ISO-8859-1')
    
    def write_ascii(self, value: str) -> None:
        "Write value encoded with ISO-8859-1, then write an additional 0x00 at the end."
        self.write(bytearray(value, 'ISO-8859-1'))
        self.write(bytearray.fromhex('00'))
    
    def read_short(self) -> int:
        """-32768 - 32767.
        Read two bytes from self and unpack with format h."""
        return self._unpack('h', self.read(2))
    
    def write_short(self, value: int) -> None:
        """-32768 - 32767.
        Write value packed with format h."""
        self.write(self._pack('h', value))
    
    def read_ushort(self) -> int:
        """0 - 65535.
        Read two bytes and return unpacked with format H."""
        return self._unpack('H', self.read(2))
    
    def write_ushort(self, value: int) -> None:
        """0 - 65535. Write value packed as format H."""
        self.write(self._pack('H', value))
    
    def read_int(self) -> int:
        """0 - something big. Return 4 bytes read and unpacked in format i."""
        return self._unpack('i', self.read(4))
    
    def write_int(self, value: int) -> None:
        """0 - something big. Write value packed with format i."""
        self.write(self._pack('i', value))
    
    def read_uint(self) -> int:
        """-2147483648 - 2147483647. Read 4 bytes and return unpacked with format I."""
        return self._unpack('I', self.read(4))
    
    def write_uint(self, value: int) -> None:
        """-2147483648 - 2147483647. Write value packed with format I."""
        self.write(self._pack('I', value))
    
    def read_long(self) -> int:
        """0 - something big. Read 8 bytes and return unpacked with format q."""
        return self._unpack('q', self.read(8))
    
    def write_long(self, value: int) -> None:
        """Write value packed with format q."""
        self.write(self._pack('q', value))
    
    def read_ulong(self) -> int:
        """-9223372036854775808 - 9223372036854775807.
        Read 8 bytes and return them unpacked with format Q."""
        return self._unpack('Q', self.read(8))
    
    def write_ulong(self, value: int) -> None:
        """-9223372036854775808 - 9223372036854775807.
        Write value packed with format Q."""
        self.write(self._pack('Q', value))
    
    def read_buffer(self):
        """Read a varint for length,
        then return a new connection from length read bytes."""
        length = self.read_varint()
        result = Connection()
        result.receive(self.read(length))
        return result
    
    def write_buffer(self, buffer) -> None:
        """Flush buffer, then write a varint of the length of the buffer's
        data, then write buffer data."""
        data = buffer.flush()
        self.write_varint(len(data))
        self.write(data)    

class Connection(BaseConnection):
    "Base connection class."
    def __init__(self):
        "Initialize self.send and self.received to an empty bytearray."
        self.sent = bytearray()
        self.received = bytearray()
    
    def read(self, length: int) -> bytes:
        """Return self.recieved up to length bytes, then cut recieved up to that point."""
        result = self.received[:length]
        self.received = self.received[length:]
        return result
    
    def write(self, data: bytearray) -> None:
        "Extend self.sent from data."
        if isinstance(data, Connection):
            data = data.flush()
        if isinstance(data, str):
            data = bytearray(data, 'utf-8')
        self.sent.extend(data)
    
    def receive(self, data: bytearray) -> None:
        """Extend self.received with data."""
        if not isinstance(data, bytearray):
            data = bytearray(data)
        self.received.extend(data)
    
    def remaining(self) -> int:
        """Return length of self.received."""
        return len(self.received)
    
    def flush(self) -> bytearray:
        """Return self.sent. Clears self.sent."""
        result = self.sent
        self.sent = bytearray()
        return result

class AsyncReadConnection(BaseConnection):
    "Asyncronous Read connection base class."
    async def read_varint(self) -> int:
        result = 0
        for i in range(5):
            part = (await self.read(1))[0]
            result |= (part & 0x7F) << 7 * i
            if not part & 0x80:
                return signed_int32(result).value
        raise IOError('Recieved a varint that was too big!')
    
    async def read_varlong(self) -> int:
        result = 0
        for i in range(10):
            part = (await self.read(1))[0]
            result |= (part & 0x7F) << (7 * i)
            if not part & 0x80:
                return signed_int64(result).value
        raise IOError('Recieved varlong is too big!')
    
    async def read_utf(self) -> str:
        length = await self.read_varint()
        return (await self.read(length)).decode('utf8')
    
    async def read_ascii(self) -> str:
        result = bytearray()
        while len(result) == 0 or result[-1] != 0:
            result.extend(await self.read(1))
        return result[:-1].decode('ISO-8859-1')
    
    async def read_short(self) -> int:
        return self._unpack('h', await self.read(2))
    
    async def read_ushort(self) -> int:
        return self._unpack('H', await self.read(2))
    
    async def read_int(self) -> int:
        return self._unpack('i', await self.read(4))
    
    async def read_uint(self) -> int:
        return self._unpack('I', await self.read(4))
    
    async def read_long(self) -> int:
        return self._unpack('q', await self.read(8))
    
    async def read_ulong(self) -> int:
        return self._unpack('Q', await self.read(8))
    
    async def read_buffer(self) -> int:
        length = await self.read_varint()
        result = Connection()
        result.receive(await self.read(length))
        return result

class SocketConnection(BaseConnection):
    "Socket connection."
    __slots__ = ('socket',)
    def __init__(self):
        self.socket = socket.socket()
    
    def close(self) -> None:
        "Close self."
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
    
    def __del__(self) -> None:
        "Shutdown and Close self.socket."
        self.close()

class TCPSocketConnection(SocketConnection):
    """TCP Connection to addr. Timeout defaults to 3 secconds."""
    def __init__(self, addr, timeout=3):
        """Create a connection to addr with self.socket, set TCP NODELAY to True."""
        self.socket = socket.create_connection(addr, timeout=timeout)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    
    def read(self, length: int) -> bytes:
        """Return length bytes read from self.socket. Raises IOError when server doesn't respond."""
        result = bytearray()
        while len(result) < length:
            new = self.socket.recv(length - len(result))
            if len(new) == 0:
                raise IOError('Server did not respond with any information!')
            result.extend(new)
        return result
    
    def write(self, data: bytes) -> None:
        """Send data on self.socket."""
        self.socket.send(data)

class UDPSocketConnection(SocketConnection):
    """UDP Connection to addr. Default timout is 3 secconds."""
    __slots__ = ('addr',)
    def __init__(self, addr, timeout=3):
        """Set self.addr to addr, set self.socket to new socket,
        AF_INET if IPv4, AF_INET6 otherwise."""
        self.addr = addr
        self.socket = socket.socket(
            socket.AF_INET if ip_type(addr[0]) == 4 else socket.AF_INET6,
            socket.SOCK_DGRAM,
        )
        self.socket.settimeout(timeout)
    
    def remaining(self) -> int:
        "Return 65535."
        return 65535
    
    def read(self, length: int) -> bytes:
        "Return up to self.remaining() bytes. Length does nothing."
        result = bytearray()
        while len(result) == 0:
            result.extend(self.socket.recvfrom(self.remaining())[0])
        return result
    
    def write(self, data: bytes) -> None:
        "Use self.socket to send data to self.addr."
        if isinstance(data, BaseConnection):
            data = bytearray(data.flush())
        self.socket.sendto(data, self.addr)

class TCPAsyncSocketConnection(AsyncReadConnection):
    "Asyncronous TCP connection to addr. Default timeout is 3 secconds."
    __slots__ = 'reader', 'writer'
    def __init__(self):
        self.reader = None
        self.writer = None
    
    async def connect(self, addr, timeout=3) -> None:
        "Use asyncio to open a connection to addr (host, port)."
        conn = asyncio.open_connection(addr[0], addr[1])
        self.reader, self.writer = await asyncio.wait_for(conn, timeout=timeout)
    
    async def read(self, length: int) -> bytes:
        "Read up to length bytes from self.reader."
        result = bytearray()
        while len(result) < length:
            new = await self.reader.read(length - len(result))
            if len(new) == 0:
                raise IOError('Server did not respond with any information!')
            result.extend(new)
        return result
    
    def write(self, data: bytes) -> None:
        "Write data to self.writer."
        self.writer.write(data)
    
    def close(self) -> None:
        "Close self.writer."
        if hasattr(self.writer, 'close'):
            self.writer.close()
        if hasattr(self.reader, 'close'):
            self.reader.close()
    
    def __del__(self) -> None:
        "Close self."
        self.close()

class UDPAsyncSocketConnection(AsyncReadConnection):
    """Asyncronous UDP connection to addr. Default timeout is 3 secconds."""
    __slots__ = 'stream', 'timeout'
    def __init__(self):
        self.stream = None
        self.timeout = None
    
    async def connect(self, addr: tuple, timeout: int=3) -> None:
        "Connect to addr (host, port)"
        self.timeout = timeout
        conn = asyncio_dgram.connect((addr[0], addr[1]))
        self.stream = await asyncio.wait_for(conn, timeout=self.timeout)
    
    def remaining(self) -> int:
        "Return 65535."
        #2 ** 16 - 1
        return 65535
    
    async def read(self, length: int) -> bytes:
        "Read from stream. Length does nothing."
        data, remote_addr = await asyncio.wait_for(self.stream.recv(),
                                                   timeout=self.timeout)
        return data
    
    async def write(self, data: bytes) -> None:
        """Send data with self.stream."""
        if isinstance(data, BaseConnection):
            data = bytearray(data.flush())
        await self.stream.send(data)
    
    def close(self) -> None:
        "Close self.stream"
        self.stream.socket.shutdown(socket.SHUT_RDWR)
        self.stream.socket.close()
        self.stream.close()
    
    def __del__(self) -> None:
        """Close self.stream."""
        try:
            self.close()
        except (asyncio.exceptions.CancelledError,
                asyncio.exceptions.TimeoutError):
            return
