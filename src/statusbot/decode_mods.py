"""Decode Mod Data - Decode forgeData tag."""

# Programmed by CoolCat467

# Copyright 2023 CoolCat467
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from __future__ import annotations

__title__ = "Decode Mod Data"
__author__ = "CoolCat467"
__license__ = "Apache License 2.0"
__version__ = "0.0.2"


import io
from typing import TYPE_CHECKING, Any, cast

from mcstatus.protocol.connection import Connection

if TYPE_CHECKING:
    from mcstatus.status_response import RawJavaResponse


class ExtraConnection(Connection):
    """Connection but with missing boolean handlers."""

    __slots__ = ()

    def write_bool(self, value: bool) -> None:
        """Write 1 byte for boolean `True` or `False`."""
        self.write(self._pack("?", value))

    def read_bool(self) -> bool:
        """Return `True` or `False`. Read 1 byte."""
        return self._unpack("?", bytes(self.read(1))) == 1


def decode_optimized(string: str) -> ExtraConnection:
    """Decode buffer from string."""
    text = io.StringIO(string)

    def read() -> int:
        result = text.read(1)
        if not result:
            return 0
        return ord(result)

    size = read() | (read() << 15)

    buffer = ExtraConnection()
    value = 0
    bits = 0
    for _ in range(len(string) - 2):
        while bits >= 8:
            buffer.receive(
                (value & 0xFF).to_bytes(
                    length=1,
                    byteorder="big",
                    signed=False,
                ),
            )
            value >>= 8
            bits -= 8
        value |= (read() & 0x7FFF) << bits
        bits += 15

    while buffer.remaining() < size:
        buffer.receive(
            (value & 0xFF).to_bytes(length=1, byteorder="big", signed=False),
        )
        value >>= 8
        bits -= 8
    return buffer


VERSION_FLAG_IGNORESERVERONLY = 0b1
# IGNORESERVERONLY = 'OHNOES\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31'
IGNORESERVERONLY = "<not required for client>"


def process_response(response: RawJavaResponse) -> dict[str, Any]:
    """Decode encoded forgeData if present."""
    data: dict[str, Any] = cast("dict[str, Any]", response)

    if "forgeData" not in response:
        return data
    forge = data["forgeData"]
    if "d" not in data:
        return data

    buffer = decode_optimized(forge["d"])

    channels: dict[tuple[str, str], tuple[str, bool]] = {}
    # channels: dict[str, tuple[str, bool]] = {}
    mods: dict[str, str] = {}

    try:
        truncated = buffer.read_bool()
        mod_size = buffer.read_ushort()
        for _ in range(mod_size):
            channel_version_flags = buffer.read_varint()

            # channel_size = signed_int32(channel_version_flags).value >> 1
            channel_size = channel_version_flags >> 1
            is_server = (
                channel_version_flags & VERSION_FLAG_IGNORESERVERONLY != 0
            )
            mod_id = buffer.read_utf()

            mod_version = IGNORESERVERONLY
            if not is_server:
                mod_version = buffer.read_utf()

            for _ in range(channel_size):
                name = buffer.read_utf()
                version = buffer.read_utf()
                client_required = buffer.read_bool()
                # channels[f'{mod_id}:{name}'] = (version, client_required)
                channels[(mod_id, name)] = (version, client_required)

            mods[mod_id] = mod_version

        non_mod_channel_size = buffer.read_varint()
        for _ in range(non_mod_channel_size):
            mod_name, mod_id = buffer.read_utf().split(":", 1)
            channel_key: tuple[str, str] = mod_name, mod_id
            # name = buffer.read_utf()
            version = buffer.read_utf()
            client_required = buffer.read_bool()
            # channels[name] = (version, client_required)
            channels[channel_key] = (version, client_required)
    except Exception as ex:
        if not truncated:
            print(
                f"Encountered {ex!r} decoding forge response, "
                "silently ignoring",
            )
        # Semi-expect errors if truncated

    new_forge = {}
    for k, v in forge.items():
        if k == "d":
            continue
        new_forge[k] = v
    new_forge["truncated"] = truncated
    new_forge["mods"] = mods
    new_forge["channels"] = channels
    data["forgeData"] = new_forge
    return data


if __name__ == "__main__":
    print(f"{__title__}\nProgrammed by {__author__}.\n")
