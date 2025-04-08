"""Status Bot for Discord using Python 3."""

# Programmed by CoolCat467

# Copyright 2021-2024 CoolCat467
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

__title__ = "StatusBot"
__author__ = "CoolCat467"
__license__ = "Apache License 2.0"
__version__ = "0.9.1"

import asyncio
import base64
import binascii
import concurrent.futures
import contextlib
import difflib
import inspect
import io
import json
import math
import os
import random
import sys
import traceback
from datetime import datetime
from threading import Event, Lock
from typing import TYPE_CHECKING, Any, Final, cast, get_args, get_type_hints

import discord
import mcstatus

# from discord.ext import tasks, commands
from aiohttp.client_exceptions import ClientConnectorError
from dotenv import load_dotenv

# Update talks to GitHub
# decode_mods Decodes forgeData tag
# Gears is basically like discord's Cogs, but by me.
from statusbot import decode_mods, gears, statemachine, update
from statusbot.utils import combine_end, format_time, pretty_exception_name

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Coroutine, Iterable

# https://discordpy.readthedocs.io/en/latest/index.html
# https://discord.com/developers


# import logging


# Acquire token.
# Looks for file named ".env",
# file line 1 is "# .env",
# file line 2 is "DISCORD_TOKEN=XXXXX"
load_dotenv()
TOKEN: Final = os.getenv("DISCORD_TOKEN")

BOT_PREFIX: Final = "!status"
OWNER_ID: Final = 344282497103691777
GITHUB_URL: Final = f"https://github.com/{__author__}/{__title__}"
# Branch is branch of GitHub repository to update from
BRANCH: Final = "HEAD"
SUPPORT_LINK: Final = "https://discord.gg/PuhVkTZaxt"


def write_file(filename: str, data: str) -> None:
    """Write data to file <filename>."""
    filename = os.path.abspath(filename)
    update.make_dirpath_exist(filename)
    with open(filename, "w", encoding="utf-8") as wfile:
        wfile.write(data)
        wfile.close()


def append_file(filename: str, data: str) -> None:
    """Add data to file <filename>."""
    filename = os.path.abspath(filename)
    if os.path.exists(filename):
        with open(filename, "a", encoding="utf-8") as wfile:
            wfile.write(data)
            wfile.close()
    else:
        write_file(filename, data)


def read_file(filename: str) -> str | None:
    """Read data from file <filename>. Return None if file does not exist."""
    filename = os.path.abspath(filename)
    if os.path.exists(filename):
        with open(filename, encoding="utf-8") as rfile:
            data = rfile.read()
            rfile.close()
        return data
    return None


def read_json(filename: str) -> dict[str, Any] | None:
    """Return json loads of filename read. Returns None if filename not exists."""
    filename = os.path.abspath(filename)
    if os.path.exists(filename):
        with open(filename, encoding="utf-8") as rfile:
            try:
                data: dict[str, Any] = json.load(rfile)
            except json.decoder.JSONDecodeError:
                return None
            finally:
                rfile.close()
        return data
    return None


def write_json(
    filename: str,
    dictionary: dict[str, Any],
    indent: int = 2,
) -> None:
    """Write dictionary as json to filename."""
    filename = os.path.abspath(filename)
    update.make_dirpath_exist(filename)
    with open(filename, "w", encoding="utf-8") as wfile:
        try:
            json.dump(dictionary, wfile, indent=indent)
        finally:
            wfile.close()


def parse_args(string: str, ignore: int = 0, sep: str = " ") -> list[str]:
    """Return a list of arguments."""
    return string.split(sep)[ignore:]


def wrap_list_values(items: Iterable[str], wrap: str = "`") -> list[str]:
    """Wrap all items in list of strings with wrap. Ex. ['cat'] -> ['`cat`']."""
    return [f"{wrap}{item}{wrap}" for item in items]


def closest(given: str, options: Iterable[str]) -> str:
    """Get closest text to given from options."""
    return difflib.get_close_matches(given, options, n=1, cutoff=0)[0]


def log_active_exception(
    logpath: str | None = None,
    extra: str | None = None,
) -> None:
    """Log active exception."""
    # Get values from exc_info
    values = sys.exc_info()
    # Get error message.
    msg = "#" * 16 + "\n"
    if extra is not None:
        msg += f"{extra}\n"
    msg += "Exception class:\n" + str(values[0]) + "\n"
    msg += "Exception text:\n" + str(values[1]) + "\n"

    with io.StringIO() as yes_totally_a_file:
        traceback.print_exception(
            None,
            value=values[1],
            tb=values[2],
            limit=None,
            file=yes_totally_a_file,
            chain=True,
        )
        msg += "\n" + yes_totally_a_file.getvalue() + "\n" + "#" * 16 + "\n"
    print(msg)
    if logpath is not None:
        append_file(logpath, msg)


def get_valid_options(valid: Iterable[str], wrap: str = "`") -> str:
    """Return string of ' Valid options are: {valid}' with pretty formatting."""
    validops = combine_end(wrap_list_values(valid, wrap))
    return f" Valid options are: {validops}."


def union_match(argument_type: type, target_type: type) -> bool:
    """Return if argument type or optional of argument type is target type."""
    return argument_type == target_type or argument_type in get_args(
        target_type,
    )


def process_arguments(
    parameters: dict[str, type],
    given_args: list[str],
    message: discord.message.Message,
) -> dict[str, Any]:
    """Process arguments to on_message handler."""
    complete: dict[str, Any] = {}
    if not parameters:
        return complete

    required_count = 0
    for v in parameters.values():
        if type(None) not in get_args(v):
            required_count += 1

    if len(given_args) < required_count:
        raise ValueError("Missing parameters!")

    i = -1
    for name, target_type in parameters.items():
        i += 1
        arg = None if i >= len(given_args) else given_args[i]
        arg_type = type(arg)
        if union_match(arg_type, target_type):
            complete[name] = arg
            continue
        if union_match(arg_type, str):
            assert isinstance(arg, str)
            matched = False
            if message.guild is not None:
                if union_match(target_type, discord.VoiceChannel):
                    for voice_channel in message.guild.voice_channels:
                        if voice_channel.name == arg:
                            complete[name] = voice_channel
                            matched = True
                            break
                if union_match(target_type, discord.TextChannel):
                    for text_channel in message.guild.text_channels:
                        if text_channel.name == arg:
                            complete[name] = text_channel
                            matched = True
                            break
            if union_match(target_type, float) and arg.isdecimal():
                complete[name] = float(arg)
                continue
            if union_match(target_type, int) and arg.isdigit():
                complete[name] = int(arg)
                continue
            if matched:
                continue
        raise ValueError
    if parameters and union_match(target_type, str) and i < len(given_args):
        complete[name] += " " + " ".join(given_args[i:])
    return complete


def override_methods(obj: Any, attrs: dict[str, Any]) -> Any:
    """Override attributes of object."""

    class OverrideGetattr:
        """Override get attribute."""

        def __getattr__(self, attr_name: str, /, default: Any = None) -> Any:
            """Get attribute but maybe return proxy of attribute."""
            if attr_name not in attrs:
                if default is None:
                    return getattr(obj, attr_name)
                return getattr(obj, attr_name, default)
            return attrs[attr_name]

        # def __setattr__(self, attr_name: str, value: Any) -> None:
        #     setattr(obj, attr_name, value)
        def __repr__(self) -> str:
            return f"Overwritten {obj!r}"

    override = OverrideGetattr()
    for attr in dir(obj):
        if attr not in attrs and not attr.endswith("__"):
            try:
                setattr(override, attr, getattr(obj, attr))
            except AttributeError:
                print(attr)
    set_function_name = "__setattr__"
    setattr(
        override,
        set_function_name,
        lambda attr_name, value: setattr(obj, attr_name, value),
    )
    return override


def interaction_to_message(
    interaction: discord.Interaction[StatusBot],
    used_defer: bool = False,
) -> discord.Message:
    """Convert slash command interaction to Message."""

    def str_null(x: object | None) -> str | None:
        return None if x is None else str(x)

    data: discord.types.message.Message = {
        "id": interaction.id,
        "channel_id": interaction.channel_id or 0,
        "timestamp": "",
        # "webhook_id": None,
        "reactions": [],
        "attachments": [],
        # "activity": None,
        "embeds": [],
        "edited_timestamp": None,
        "type": 0,  # discord.MessageType.default,
        "pinned": False,
        "flags": 0,
        "mention_everyone": False,
        "tts": False,
        "content": "",
        "nonce": 0,  # Optional[Union[int, str]]
        "sticker_items": [],
        "guild_id": f"{interaction.guild_id}",
        "interaction": {
            "id": interaction.id,
            "type": 2,
            "name": "Interaction name",
            "member": {
                "deaf": (
                    str_null(interaction.user.voice.deaf)  # type: ignore[typeddict-item]
                    if isinstance(interaction.user, discord.Member)
                    and interaction.user.voice
                    else None
                ),
                "mute": (
                    str_null(interaction.user.voice.deaf)  # type: ignore[typeddict-item]
                    if isinstance(interaction.user, discord.Member)
                    and interaction.user.voice
                    else None
                ),
                "joined_at": (
                    interaction.user.joined_at.isoformat()  # type: ignore[typeddict-item]
                    if isinstance(interaction.user, discord.Member)
                    and interaction.user.joined_at
                    else None
                ),
                "premium_since": (
                    str_null(interaction.user.premium_since)
                    if isinstance(interaction.user, discord.Member)
                    else None
                ),
                "roles": (
                    []
                    if isinstance(interaction.user, discord.User)
                    else [role.id for role in interaction.user.roles]
                ),
                "nick": (
                    interaction.user.nick  # type: ignore[typeddict-item]
                    if isinstance(interaction.user, discord.Member)
                    else None
                ),
                "pending": (
                    interaction.user.pending  # type: ignore[typeddict-item]
                    if isinstance(interaction.user, discord.Member)
                    else None
                ),
                "avatar": getattr(interaction.user.avatar, "url", None),  # type: ignore[typeddict-item]
                "flags": (
                    interaction.user._flags  # type: ignore[typeddict-item]
                    if isinstance(interaction.user, discord.Member)
                    else None
                ),
                "permissions": (
                    interaction.user._permissions  # type: ignore[typeddict-item]
                    if isinstance(interaction.user, discord.Member)
                    else None
                ),
                "communication_disabled_until": (
                    str_null(  # type: ignore[typeddict-item]
                        interaction.user.timed_out_until.isoformat(),
                    )
                    if isinstance(interaction.user, discord.Member)
                    and interaction.user.timed_out_until
                    else None
                ),
            },
            "user": {
                "global_name": interaction.user.name,
                "username": interaction.user.name,
                "id": interaction.user.id,
                "discriminator": interaction.user.discriminator,
                "avatar": interaction.user._avatar,
                "bot": interaction.user.bot,
                "system": interaction.user.system,
                ##                "roles": (
                ##                    []
                ##                    if isinstance(interaction.user, discord.User)
                ##                    else [role.id for role in interaction.user.roles]
                ##                ),
            },
        },
        # 'message_reference': None,
        "application": {
            "id": interaction.application_id,
            "description": "Application description",
            "name": "Application name",
            "icon": None,
            "cover_image": "Cover Image",
        },
        # 'author': interaction.user,
        # 'member'       : ,
        "mentions": [],
        "mention_roles": [],
        # 'components'   :
    }

    message = discord.message.Message(
        state=interaction._state,
        channel=interaction.channel,  # type: ignore
        data=data,
    )

    message.author = interaction.user

    channel_send = message.channel.send
    times = -1

    async def send_message(*args: Any, **kwargs: Any) -> Any:
        """Send message."""
        nonlocal times
        times += 1
        if times == 0 and used_defer:
            return await interaction.followup.send(*args, **kwargs)
        if not interaction.response.is_done():
            return await interaction.response.send_message(*args, **kwargs)
            # return await interaction.response.edit_message(*args, **kwargs)
        return await channel_send(*args, **kwargs)

    message.channel = override_methods(
        message.channel,
        {
            "send": send_message,
        },
    )

    return message


def extract_parameters_from_callback(
    func: Callable[..., Any],
    globalns: dict[str, Any],
) -> dict[str, discord.app_commands.transformers.CommandParameter]:
    """Set up slash command things from function.

    Stolen from internals of discord.app_commands.commands
    """
    params = inspect.signature(func).parameters
    cache: dict[str, Any] = {}
    required_params = 1
    if len(params) < required_params:
        raise TypeError(
            f"callback {func.__qualname__!r} must have more "
            f"than {required_params - 1} parameter(s)",
        )

    iterator = iter(params.values())
    for _ in range(required_params):
        next(iterator)

    parameters: list[discord.app_commands.transformers.CommandParameter] = []
    for parameter in iterator:
        if parameter.annotation is parameter.empty:
            raise TypeError(
                f"parameter {parameter.name!r} is missing a "
                f"type annotation in callback {func.__qualname__!r}",
            )

        resolved = discord.utils.resolve_annotation(
            parameter.annotation,
            globalns,
            globalns,
            cache,
        )
        param = discord.app_commands.transformers.annotation_to_parameter(
            resolved,
            parameter,
        )
        parameters.append(param)

    values = sorted(parameters, key=lambda a: a.required, reverse=True)
    result = {v.name: v for v in values}

    descriptions = discord.app_commands.commands._parse_args_from_docstring(
        func,
        result,
    )

    try:
        name = "__discord_app_commands_param_description__"
        descriptions.update(getattr(func, name))
    except AttributeError:
        for param in values:
            if param.description is discord.utils.MISSING:
                param.description = "…"
    if descriptions:
        discord.app_commands.commands._populate_descriptions(
            result,
            descriptions,
        )

    try:
        renames = func.__discord_app_commands_param_rename__  # type: ignore
    except AttributeError:
        pass
    else:
        discord.app_commands.commands._populate_renames(result, renames.copy())

    try:
        choices = func.__discord_app_commands_param_choices__  # type: ignore
    except AttributeError:
        pass
    else:
        discord.app_commands.commands._populate_choices(result, choices.copy())

    try:
        name = "__discord_app_commands_param_autocomplete__"
        autocomplete = getattr(func, name)
    except AttributeError:
        pass
    else:
        discord.app_commands.commands._populate_autocomplete(
            result,
            autocomplete.copy(),
        )

    return result


def slash_handle(
    message_command: Callable[[discord.Message], Awaitable[None]],
    should_defer: bool = False,
) -> tuple[
    Callable[[discord.Interaction[StatusBot]], Coroutine[Any, Any, Any]],
    Any,
]:
    """Slash handle wrapper to convert interaction to message."""

    class Dummy:
        """Dummy class so required_params = 2 for slash_handler."""

        async def slash_handler(
            *args: discord.Interaction[StatusBot],
            **kwargs: Any,
        ) -> None:
            """Slash command wrapper for message-based command."""
            interaction: discord.Interaction[StatusBot] = args[1]
            if should_defer:
                # Defer response
                await interaction.response.defer()
            try:
                msg = interaction_to_message(interaction, should_defer)
            except Exception:
                root = os.path.split(os.path.abspath(__file__))[0]
                logpath = os.path.join(root, "log.txt")
                log_active_exception(logpath)
                raise
            try:
                if isinstance(
                    interaction.command,
                    discord.app_commands.commands.Command,
                ):
                    name = ""
                    with contextlib.suppress(Exception):
                        name = interaction.user.name
                    timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                    print(
                        f"[{timestamp}] Slash Command: {interaction.command.name!r} Args: {kwargs} from {name!r}",
                    )
                await message_command(msg, *args[2:], **kwargs)
            except Exception:
                await msg.channel.send(
                    "An error occurred processing the slash command",
                )
                if hasattr(interaction._client, "on_error"):
                    await interaction._client.on_error(
                        "slash_command",
                        message_command.__name__,
                    )
                raise

    params = extract_parameters_from_callback(
        message_command,
        message_command.__globals__,
    )
    merp = Dummy()
    return merp.slash_handler, params  # type: ignore


async def send_over_2000(
    send_func: Callable[[str], Awaitable[None]],
    text: str,
    header: str = "",
    wrap_with: str = "",
    start: str = "",
) -> None:
    """Use send_func to send text in segments if required."""
    parts = [start + wrap_with + header]
    send = str(text)
    wrap_alloc = len(wrap_with)
    while send:
        cur_block = len(parts[-1])
        if cur_block < 2000:
            end = 2000 - (cur_block + wrap_alloc)
            add = send[0:end]
            send = send[end:]
            parts[-1] += add + wrap_with
        else:
            parts.append(wrap_with + header)

    # pylint: disable=wrong-spelling-in-comment
    # This would be great for asyncio.gather, but
    # I'm pretty sure that will throw off call order,
    # and it's quite important that everything stays in order.
    # coros = [send_func(part) for part in parts]
    # await asyncio.gather(*coros)
    for part in parts:
        await send_func(part)


async def send_command_list(
    commands: dict[
        str,
        Callable[[discord.message.Message], Coroutine[None, None, None]],
    ],
    name: str,
    channel: discord.abc.Messageable,
) -> None:
    """Send message on channel telling user about all valid name commands."""
    sort = sorted(commands.keys(), reverse=True)
    command_data = [f"`{v}` - {commands[v].__doc__}" for v in sort]
    await send_over_2000(
        channel.send,  # type: ignore
        "\n".join(command_data),
        start=f"{__title__}'s Valid {name} Commands:\n",
    )


async def get_github_file(path: str, timeout: int = 10) -> str:
    """Return text from GitHub file in this project decoded as utf-8."""
    file = await update.get_file(__title__, path, __author__, BRANCH, timeout)
    value = file.decode("utf-8")
    assert isinstance(value, str)
    return value


class GuildServerPinger(gears.StateTimer):
    """Server ping machine for guild."""

    __slots__ = (
        "channel",
        "guild_id",
        "last_delay",
        "last_json",
        "last_online",
        "last_online",
        "last_online_count",
        "server",
    )
    tick_speed: int = 60
    wait_ticks: int = 5

    def __init__(self, bot: StatusBot, guild_id: int) -> None:
        """Needs bot we work for, and id of guild we are pinging the server for."""
        self.guild_id = guild_id
        super().__init__(bot, str(self.guild_id), self.tick_speed)
        self.server: mcstatus.JavaServer
        self.bot: StatusBot
        self.last_json: dict[str, Any] = {}
        self.last_delay: int | float = 0
        self.last_online: list[str] = []
        self.last_online_count: int = 0
        self.channel: discord.abc.Messageable

        self.add_state(PingState())
        self.add_state(WaitRestartState(self.wait_ticks))

    @property
    def wait_time(self) -> int:
        """Total wait time when in await_restart state."""
        return self.tick_speed * self.wait_ticks

    async def initialize_state(self) -> None:
        """Set state to ping."""
        await self.set_state("ping")

    async def start(self) -> None:
        """If configuration is good, run."""
        configuration = self.bot.get_guild_configuration(self.guild_id)
        channel = self.bot.guess_guild_channel(self.guild_id)
        if channel is None:
            print(
                f"[{self.__class__.__name__} start] Channel for {self.guild_id!r} is None, not starting.",
            )
            await self.set_state("Hault")
            return
        self.channel = channel
        if "address" not in configuration:
            await self.channel.send(
                "No address for this guild defined, pinger not started.",
            )
            await self.set_state("Hault")
            return
        try:
            self.server = await mcstatus.JavaServer.async_lookup(
                configuration["address"],
            )
        except Exception as exc:  # pylint: disable=broad-except
            error = pretty_exception_name(exc)
            with contextlib.suppress(ClientConnectorError):
                await send_over_2000(
                    cast(
                        "Callable[[str], Awaitable[None]]",
                        self.channel.send,
                    ),
                    text=error,
                    wrap_with="```",
                    start="An error occurred resolving DNS address:",
                )
                await self.channel.send("Server pinger stopped.")
            await self.set_state("Hault")
            return
        try:
            await super().start()
        except Exception:  # pylint: disable=broad-except
            log_active_exception(self.bot.logpath)
        finally:
            with contextlib.suppress(ClientConnectorError):
                await self.channel.send("Server pinger stopped.")
            await self.set_state("Hault")


class PingState(statemachine.AsyncState[GuildServerPinger]):
    """State where we ping server."""

    __slots__ = ("exit_ex", "failed", "failures_in_row")

    fail_threshold = 2

    def __init__(self) -> None:
        """Initialize Ping State."""
        super().__init__("ping")

        self.failed = False
        self.exit_ex: str | None = None
        self.failures_in_row = 0

    async def entry_actions(self) -> None:
        """Reset failed to false and exception to None."""
        self.failed = False
        self.exit_ex = None
        self.failures_in_row = 0
        self.machine.last_delay = math.inf
        self.machine.last_online.clear()

    async def handle_sample(self, players: list[str]) -> None:
        """Handle change in players by players sample."""
        # If different players,
        if players == self.machine.last_online:
            return

        # Find difference in players.
        players_set = set(players) - {"Anonymous Player"}
        last_set = set(self.machine.last_online) - {"Anonymous Player"}
        joined = tuple(players_set.difference(last_set))
        left = tuple(last_set.difference(players_set))

        # Find difference in anonymous players
        anonymous_players = players.count("Anonymous Player")
        last_anonymous_players = self.machine.last_online.count(
            "Anonymous Player",
        )
        anonymous_delta = anonymous_players - last_anonymous_players
        anonymous_joined = max(0, anonymous_delta)
        anonymous_left = abs(min(0, anonymous_delta))

        if anonymous_joined:
            extra = "" if anonymous_joined < 2 else f"{anonymous_joined}x "
            joined += (f"{extra}Anonymous Player",)
        if anonymous_left:
            extra = "" if anonymous_left < 2 else f"{anonymous_left}x "
            left += (f"{extra}Anonymous Player",)

        def users_mesg(action: str, users: Iterable[str]) -> str:
            """Return [{action}]: {users}."""
            text = f"[{action}]:\n"
            text += combine_end(wrap_list_values(users, "`"))
            return text

        # Collect left and joined messages.
        message = ""
        if left:
            message = users_mesg("Left", left)
        if joined:
            if message:
                message += "\n"
            message += users_mesg("Joined", joined)
        # Send message to guild channel.
        if message:
            await send_over_2000(
                cast(
                    "Callable[[str], Awaitable[None]]",
                    self.machine.channel.send,
                ),
                message,
            )

    async def handle_count(self, online: int) -> None:
        """Handle change in players by online count."""
        # Otherwise, server with player sample disabled
        # and can only tell number of left/joined
        if online == self.machine.last_online_count:
            # If same, no need
            return
        diff = online - self.machine.last_online_count
        if diff == 0:
            return
        player = "player" if diff == 1 else "players"
        if diff > 0:
            await self.machine.channel.send(f"[Joined]: {diff} {player}")
        else:
            await self.machine.channel.send(f"[Left]: {-diff} {player}")

    async def do_actions(self) -> None:
        """Ping server. If failure, self.failed = True and if exceptions, save."""
        try:
            response = await self.machine.server.async_status()
        except Exception as exc:  # pylint: disable=broad-except
            error = pretty_exception_name(exc)
            self.exit_ex = f"`A {error} Error Has Occored"
            if exc.args:
                sargs = list(map(str, exc.args))
                self.exit_ex += ": " + combine_end(
                    wrap_list_values(sargs, '"'),
                )
            self.exit_ex += "`"
            # No need to record detailed errors for timeouts.
            ignore = (
                concurrent.futures.TimeoutError,
                asyncio.exceptions.TimeoutError,
                ConnectionRefusedError,
                IOError,
            )
            self.failures_in_row += 1
            if not isinstance(exc, ignore):
                self.failed = True
                log_active_exception(self.machine.bot.logpath)
            else:
                self.failed = self.failures_in_row >= self.fail_threshold
            return
        else:
            self.failures_in_row = 0
        json_data = decode_mods.process_response(response.raw)
        ping = round(response.latency, 3)
        # If success, get players.
        self.machine.last_json = json_data
        self.machine.last_delay = ping

        players: list[str] = []
        online = 0

        if "players" not in json_data:
            # Update last ping.
            self.machine.last_online = players
            return

        if "online" in json_data["players"]:
            online = json_data["players"]["online"]
        if "sample" in json_data["players"]:
            for player in json_data["players"]["sample"]:
                if "name" in player:
                    players.append(player["name"])

        if not players and online:
            await self.handle_count(online)
            self.machine.last_online_count = online
        else:
            await self.handle_sample(players)
            # Update last ping.
            self.machine.last_online = players
        self.machine.last_online_count = max(online, len(players))

    async def check_conditions(self) -> str | None:
        """If there was failure to connect to server, await restart."""
        if self.failed:
            return "await_restart"
        return None

    async def exit_actions(self) -> None:
        """When exiting, if we collected an exception, send it to channel."""
        if self.exit_ex is not None:
            with contextlib.suppress(discord.errors.Forbidden):
                await self.machine.channel.send(self.exit_ex)


class WaitRestartState(statemachine.AsyncState[GuildServerPinger]):
    """State where we wait for server to restart."""

    __slots__ = ("ignore_ticks", "ping", "success", "ticks")

    def __init__(self, ignore_ticks: int) -> None:
        """Initialize await_restart state."""
        super().__init__("await_restart")
        self.ignore_ticks = ignore_ticks
        self.success = False
        self.ticks = 0
        self.ping: int | float = 0

    async def entry_actions(self) -> None:
        """Reset failed and say connection lost."""
        extra = ""
        if self.machine.last_delay not in {math.inf, 0}:
            extra = (
                " Last successful ping latency was "
                f"`{self.machine.last_delay}ms`"
            )
        await self.machine.channel.send(
            "Connection to server has been lost." + extra,
        )
        self.success = False
        self.ticks = 0
        self.ping = 0

    async def attempt_contact(self) -> bool:
        """Attempt to talk to server."""
        try:
            self.ping = await self.machine.server.async_ping()
        except Exception:  # pylint: disable=broad-except  # noqa: S110
            pass
        else:
            return True
        return False

    async def do_actions(self) -> None:
        """Every once and a while try to talk to server again."""
        self.ticks = (self.ticks + 1) % self.ignore_ticks

        if self.ticks == 0:
            self.success = await self.attempt_contact()

    async def check_conditions(self) -> str | None:
        """If contact attempt was successfully, switch back to ping."""
        if self.success:
            return "ping"
        return None

    async def exit_actions(self) -> None:
        """Perform exit actions."""
        if self.success:
            await self.machine.channel.send(
                "Connection to server re-established "
                f"with a ping of `{self.ping}ms`.",
            )
        else:
            try:
                await self.machine.channel.send(
                    "Could not re-establish connection to server.",
                )
            except discord.errors.Forbidden:
                print("Cannot send message in lost guild")


class StatusBot(
    discord.Client,
    gears.BaseBot,
):  # pylint: disable=too-many-public-methods,too-many-instance-attributes
    """StatusBot needs prefix, event loop, and any arguments to pass to discord.Client."""

    def __init__(
        self,
        prefix: str,
        loop: asyncio.AbstractEventLoop,
        *args: Any,
        intents: discord.Intents,
        **kwargs: Any,
    ) -> None:
        """Initialize StatusBot."""
        self.loop = loop

        discord.Client.__init__(
            self,
            *args,
            loop=self.loop,
            intents=intents,
            **kwargs,
        )
        self.stopped = Event()
        self.updating = Lock()
        self.prefix = prefix
        self.rootdir = os.path.dirname(os.path.abspath(__file__))
        self.logpath = os.path.join(self.rootdir, "log.txt")
        self.gcommands: dict[
            str,
            Callable[[discord.message.Message], Coroutine[Any, Any, Any]],
        ] = {
            "current-version": self.current_vers,
            "support": self.support,
            "online-version": self.online_vers,
            "my-id": self.my_id,
            "json": self.json,
            "favicon": self.favicon,
            "online": self.online,
            "ping": self.ping,
            "forge-mods": self.forge_mods,
            "refresh": self.refresh,
            "set-option": self.set_option__guild,  # type: ignore[dict-item]
            "get-option": self.get_option__guild,
            "help": self.help_guild,
        }
        self.dcommands: dict[
            str,
            Callable[[discord.message.Message], Coroutine[Any, Any, Any]],
        ] = {
            "current-version": self.current_vers,
            "support": self.support,
            "online-version": self.online_vers,
            "my-id": self.my_id,
            "stop": self.stop,
            "update": self.update,
            "set-global-option": self.set_option__dm,
            "get-global-option": self.get_option__dm,
            "global-help": self.help_dm,
            "system-alert": self.system_alert,
        }
        gears.BaseBot.__init__(self, self.loop)

        self.tree = discord.app_commands.CommandTree(self)
        for command_group, dm_only in (
            (self.gcommands, False),
            (self.dcommands, True),
        ):
            for command_name, command_function in command_group.items():
                if dm_only and command_name in self.gcommands:
                    continue
                callback, params = slash_handle(command_function)
                command: discord.app_commands.commands.Command[
                    Any,
                    Any,
                    None,
                ] = discord.app_commands.commands.Command(
                    name=command_name,
                    description=command_function.__doc__ or "",
                    callback=callback,
                    nsfw=False,
                    auto_locale_strings=True,
                )
                if dm_only:
                    command = discord.app_commands.dm_only(command)
                elif command_name not in self.dcommands:
                    command = discord.app_commands.guild_only(command)
                command._params = params
                command.checks = getattr(
                    callback,
                    "__discord_app_commands_checks__",
                    [],
                )
                command._guild_ids = getattr(
                    callback,
                    "__discord_app_commands_default_guilds__",
                    None,
                )
                command.default_permissions = getattr(
                    callback,
                    "__discord_app_commands_default_permissions__",
                    None,
                )
                command.guild_only = getattr(
                    callback,
                    "__discord_app_commands_guild_only__",
                    False,
                )
                command.binding = getattr(command_function, "__self__", None)
                self.tree.add_command(command)
        self.tree.on_error = self.on_error  # type: ignore[assignment]

    def __repr__(self) -> str:
        """Return representation of self."""
        #     up = self.__class__.__weakref__.__qualname__.split('.')[0]
        return f"<{self.__class__.__name__} Object>"  # ({up} subclass)>'

    @property
    def gear_close(self) -> bool:
        """Return True if gears should close."""
        return self.stopped.is_set() or self.is_closed()

    async def wait_ready(self) -> None:
        """Define wait for gears BaseBot."""
        await self.wait_until_ready()

    def get_guild_configuration_file(self, guild_id: int) -> str:
        """Return the path to the configuration json file for a certain guild."""
        return os.path.join(
            self.rootdir,
            "config",
            "guilds",
            str(guild_id) + ".json",
        )

    def get_dm_configuration_file(self) -> str:
        """Return the path to the configuration file."""
        return os.path.join(self.rootdir, "config", "dms.json")

    def get_guild_configuration(self, guild_id: int) -> dict[str, Any]:
        """Return a dictionary from the json read from guild configuration file."""
        guildfile = self.get_guild_configuration_file(guild_id)
        guildconfiguration = read_json(guildfile)
        if guildconfiguration is None:
            # Guild does not have configuration
            # Therefore, create file for them
            write_file(guildfile, "{}")
            guildconfiguration = {}
        return guildconfiguration

    def get_dm_configuration(self) -> dict[str, Any]:
        """Return a dictionary from configuration file."""
        dmfile = self.get_dm_configuration_file()
        dmconfiguration = read_json(dmfile)
        if dmconfiguration is None:
            write_file(dmfile, "{}")
            dmconfiguration = {}
        return dmconfiguration

    def write_guild_configuration(
        self,
        guild_id: int,
        configuration: dict[str, Any],
    ) -> None:
        """Write guild configuration file from configuration dictionary."""
        guildfile = self.get_guild_configuration_file(guild_id)
        write_file(guildfile, json.dumps(configuration, indent=2))

    def write_dm_configuration(self, configuration: dict[str, Any]) -> None:
        """Write configuration file from configuration dictionary."""
        dmfile = self.get_dm_configuration_file()
        write_file(dmfile, json.dumps(configuration, indent=2))

    def guess_guild_channel(self, gid: int) -> discord.abc.Messageable | None:
        """Guess guild channel and return channel. Return None on failure."""
        guild = self.get_guild(gid)
        if guild is None:
            raise RuntimeError(f"Could not get guild of id `{gid}`")
        configuration = self.get_guild_configuration(gid)
        valid = [chan.name for chan in guild.text_channels]
        if "channel" in configuration:
            channelname = configuration["channel"]
            if channelname in valid:
                channel = discord.utils.get(
                    guild.text_channels,
                    name=channelname,
                )
                if channel is not None:
                    return channel
        expect = [cname for cname in valid if "bot" in cname.lower()]
        expect += ["general"]
        for channel in guild.text_channels:
            if channel.name in expect:
                return channel
        if not guild.text_channels:
            return None
        return random.choice(guild.text_channels)  # noqa: S311

    async def search_for_member_in_guilds(
        self,
        username: str,
    ) -> discord.Member | None:
        """Search for member in all guilds we connected to.

        Return None on failure.
        """
        members = (guild.get_member_named(username) for guild in self.guilds)
        for member in members:
            if member is not None:
                return member
        return None

    async def add_guild_pinger(
        self,
        gid: int,
        force_reset: bool = False,
    ) -> str:
        """Create ping machine for guild if not exists.

        Return 'started', 'restarted', or 'none'.
        """
        gear = self.get_gear(str(gid))
        if gear is None:
            self.add_gear(GuildServerPinger(self, gid))
            return "started"
        if force_reset or not gear.running:
            if not gear.stopped:
                await gear.hault()
            self.remove_gear(str(gid))
            self.add_gear(GuildServerPinger(self, gid))
            return "restarted"
        return "none"

    ##async def register_commands(self, guild: discord.Guild) -> None:
    ##    """Register commands for guild."""
    ##    #self.tree.copy_global_to(guild=guild)
    ##
    ##    await self.tree.sync(guild=guild)

    async def eval_guild(
        self,
        guild_id: int,
        force_reset: bool = False,
    ) -> int:
        """(Re)Start guild machine if able or alert need of settings change."""
        guildconfiguration = self.get_guild_configuration(guild_id)
        channel = self.guess_guild_channel(guild_id)
        if channel is None:
            print(
                f"[eval_guild] Channel is None for guild {guild_id!r}, strange case.",
            )
            return guild_id
        with contextlib.suppress(discord.errors.Forbidden):
            if "channel" not in guildconfiguration:
                await channel.send(
                    "This is where I will post join-leave messages "
                    "until an admin sets my `channel` option. "
                    f"Set it with `{self.prefix} set-option channel <channel>`.",
                )
            if "address" in guildconfiguration:
                action = await self.add_guild_pinger(guild_id, force_reset)
                if action != "none":
                    await channel.send(f"Server pinger {action}.")
                else:
                    await channel.send(
                        "Server pinger is still running, non-critical configuration change.",
                    )
            else:
                await channel.send(
                    "Server address not set, pinger not started. "
                    f"Please set it with `{self.prefix} set-option "
                    "address <address>`.",
                )
        return guild_id

    async def eval_guilds(self, force_reset: bool = False) -> list[int]:
        """Evaluate all guilds. Return list of guild ids evaluated."""
        ids = []
        # register = []
        for guild in self.guilds:
            # register.append(self.register_commands(guild))
            ids.append(self.eval_guild(guild.id, force_reset))
        # await asyncio.gather(*register)
        return await asyncio.gather(*ids)

    # Default, not affected by intents.
    async def on_ready(self) -> None:
        """Print information about bot and evaluate all guilds."""
        print(f"{self.user} has connected to Discord!")
        print(f"Prefix  : {self.prefix}")
        print(f"Intents : {self.intents}")
        print(f"Root Dir: {self.rootdir}")

        configurationdir = os.path.join(self.rootdir, "config")
        if not os.path.exists(configurationdir):
            os.mkdir(configurationdir)
        guilddir = os.path.join(configurationdir, "guilds")
        if not os.path.exists(guilddir):
            os.mkdir(guilddir)

        print(f"\n{self.user} is connected to the following guilds:\n")
        guildnames = []
        for guild in self.guilds:
            guildnames.append(f"{guild.name} (id: {guild.id})")
        spaces = max(len(name) for name in guildnames)
        print(
            "\n".join(name.rjust(spaces) for name in guildnames) + "\n",
        )

        ids = await self.eval_guilds(True)

        print("Guilds evaluated:\n" + "\n".join([str(x) for x in ids]) + "\n")

        synced = await self.tree.sync()
        print(f"{len(synced)} slash commands synced\n")

        act = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"for {self.prefix}",
        )
        await self.change_presence(status=discord.Status.online, activity=act)

    async def replace_ids_w_names(
        self,
        names: Iterable[str | int],
    ) -> list[str]:
        """Replace user ids (integers) with usernames in lists.

        Returns list of strings.
        """
        replaced = []
        for item in names:
            if isinstance(item, int):
                user = self.get_user(item)
                # # Slower but does not require members intent
                # user = self.fetch_user(item)
                if user is not None:
                    replaced.append(f"{user.name} (id. {item})")
                    continue
            replaced.append(str(item))
        return replaced

    async def my_id(self, message: discord.message.Message) -> None:
        """Tells you your user id."""
        await message.channel.send(f"Your user id is `{message.author.id}`.")

    async def ensure_pinger_good(
        self,
        message: discord.message.Message,
    ) -> GuildServerPinger | None:
        """Return GuildServerPinger if pinger is working properly, else None."""
        if message.guild is None:
            await message.channel.send(
                "Message guild is `None`, this is an error."
                f"Please report at {GITHUB_URL}/issues.",
            )
            raise ValueError("Message guild is None")
        gear = self.get_gear(str(message.guild.id))
        if gear is None:
            await message.channel.send(
                "Server pinger is not running for this guild. "
                "Use command `refresh` to restart.",
            )
            return None
        assert isinstance(gear, GuildServerPinger)
        pinger: GuildServerPinger = gear
        if pinger.active_state is None:
            await message.channel.send(
                "Server pinger is not active for this guild. "
                + "Use command `refresh` to restart.",
            )
            return None
        if pinger.active_state.name != "ping":
            delay = format_time(pinger.wait_time)
            await message.channel.send(
                f"Cannot connect to server at this time, try again in {delay}.",
            )
            return None
        return pinger

    async def favicon(self, message: discord.message.Message) -> None:
        """Post the favicon from this guild's server."""
        pinger = await self.ensure_pinger_good(message)
        if pinger is None:
            return
        assert message.guild is not None

        if "favicon" not in pinger.last_json:
            await message.channel.send(
                "Server does not have a favicon. "
                + "Ask the server owner to add one!",
            )
            return
        favicon_data: str = pinger.last_json["favicon"]
        if not favicon_data.startswith("data:image/png;base64,"):
            await message.channel.send(
                "Server favicon is not encoded properly.",
            )
            return
        favicon_data = favicon_data.split(",")[1]
        try:
            file_handle = io.BytesIO(base64.b64decode(favicon_data))
        except binascii.Error:
            await message.channel.send(
                "Encountered error decoding base64 string for favicon.",
            )
            return
        file = discord.File(file_handle, filename=f"{message.guild.id}.png")
        await message.channel.send(file=file)
        file_handle.close()

    async def json(self, message: discord.message.Message) -> None:
        """Post the last json message from this guild's server."""
        pinger = await self.ensure_pinger_good(message)
        if pinger is None:
            return

        lastdict = pinger.last_json
        if "favicon" in lastdict:
            lastdict["favicon"] = "<base64 image data>"
        if "channels" in lastdict.get("forgeData", {}):
            lastdict["forgeData"]["channels"] = {
                ":".join(k): v
                for k, v in lastdict["forgeData"]["channels"].items()
            }
        msg = json.dumps(lastdict, sort_keys=True, indent=2)
        await send_over_2000(
            message.channel.send,  # type: ignore
            msg,
            "json\n",
            "```",
            start="Last received json message:\n",
        )

    async def ping(self, message: discord.message.Message) -> None:
        """Post the connection latency to this guild's server."""
        pinger = await self.ensure_pinger_good(message)
        if pinger is None:
            return

        msg = f"`{pinger.last_delay}ms`"
        await message.channel.send(
            f"{__title__}'s last received latency to defined guild server:\n"
            + msg,
        )

    async def forge_mods(self, message: discord.message.Message) -> None:
        """Get a list of forge mods from this guild's server if it's modded."""
        pinger = await self.ensure_pinger_good(message)
        if pinger is None:
            return

        if "forgeData" not in pinger.last_json:
            await message.channel.send(
                f"There was no forge data in {__title__}'s "
                "last received json message from this guild's server.",
            )
            return
        forge_data = pinger.last_json["forgeData"]
        if "mods" not in forge_data:  # or not 'channels' in forge_data
            await message.channel.send(
                "Error: Forge data response is missing "
                "`channels` and or `mods` field",
            )
            return

        #     channels = forge_data['channels']
        mods: dict[str, str] | list[dict[str, str]] = forge_data["mods"]

        mod_data: list[dict[str, str]] = []
        if isinstance(mods, dict):
            for name, version in mods.items():
                #         required = True
                #         if version == '<not required for client>':
                #             version = '<unknown>'
                #             required = False
                mod_item = {
                    "name": name,
                    "version": version,
                    #             'required': required
                }
                mod_data.append(mod_item)
        elif isinstance(mods, list):
            mod_data = mods

        msg = json.dumps(mod_data, sort_keys=True, indent=2)
        await send_over_2000(
            message.channel.send,  # type: ignore
            msg,
            "json\n",
            "```",
            start="Forge Mods:\n",
        )

    async def online(self, message: discord.message.Message) -> None:
        """Get the players currently connected to this guild's server."""
        pinger = await self.ensure_pinger_good(message)
        if pinger is None:
            return

        players = tuple(pinger.last_online)
        if players:
            player_text = combine_end(wrap_list_values(players, "`"))
            await send_over_2000(
                message.channel.send,  # type: ignore
                player_text,
                start="Players online in last received sample:",
            )
        elif pinger.last_online_count:
            await message.channel.send(
                f"There were `{pinger.last_online_count}` "
                "players online in last received message.",
            )
        else:
            await message.channel.send(
                "No players were online in the last received sample.",
            )

    async def stop(self, message: discord.message.Message) -> None:
        """Stop this bot."""
        configuration = self.get_dm_configuration()
        if "stop-users" not in configuration:
            await message.channel.send(
                "No one has permission to run this command.",
            )
            return

        if message.author.id in configuration["stop-users"]:
            await message.channel.send("Stopping...")
            # Set stopped event
            self.stopped.set()

            def close_bot() -> None:
                self.loop.create_task(self.close())

            self.loop.call_later(3, close_bot)
            return
        await message.channel.send(
            "You do not have permission to run this command.",
        )

    async def send_guild_system_alert(
        self,
        guild_id: int,
        alert_text: str,
    ) -> int:
        """Send guild system alert."""
        # guildconfiguration = self.get_guild_configuration(guild_id)
        channel = self.guess_guild_channel(guild_id)
        if channel is None:
            print(
                f"[eval_guild] Channel is None for guild {guild_id!r}, strange case.",
            )
            return guild_id
        with contextlib.suppress(discord.errors.Forbidden):
            await channel.send(
                f"[System Alert Message]:\n```\n{alert_text}\n```",
            )
        return guild_id

    async def system_alert(
        self,
        message: discord.message.Message,
        alert_text: str | None = None,
    ) -> None:
        """Send a system alert to all guilds."""
        configuration = self.get_dm_configuration()
        if "system-alert-users" not in configuration:
            await message.channel.send(
                "No one has permission to run this command.",
            )
            return

        if message.author.id not in configuration["system-alert-users"]:
            await message.channel.send(
                "You do not have permission to run this command.",
            )
            return

        if alert_text is None:
            await message.channel.send(
                "Please enter alert text, cannot be blank.",
            )
            return
        await message.channel.send("Sending system alert...")

        ids = []
        for guild in self.guilds:
            ids.append(self.send_guild_system_alert(guild.id, alert_text))

        finished = await asyncio.gather(*ids)

        msg = json.dumps(finished, sort_keys=True, indent=2)
        await send_over_2000(
            message.channel.send,  # type: ignore
            msg,
            "json\n",
            "```",
            start="Sent alert text to following guild ids:\n",
        )

    async def current_vers_channel(
        self,
        messageable: discord.abc.Messageable,
    ) -> tuple[int, ...]:
        """Send and return this instance of StatusBot's version."""
        proj_root = os.path.dirname(os.path.dirname(self.rootdir))
        version = read_file(os.path.join(proj_root, "version.txt"))
        await messageable.send(f"Current version: {version}")
        if not version:
            return tuple(map(int, __version__.strip().split(".")))
        return tuple(map(int, version.strip().split(".")))

    async def current_vers(
        self,
        message: discord.message.Message,
    ) -> tuple[int, ...]:
        """Get the version of this instance of StatusBot."""
        return await self.current_vers_channel(message.channel)

    async def support(
        self,
        message: discord.message.Message,
    ) -> None:
        """Get link to the Official StatusBot Support Server."""
        await message.channel.send(
            f"Support Server Guild Link: {SUPPORT_LINK}",
        )

    async def online_vers(
        self,
        message: discord.message.Message,
    ) -> tuple[int, ...]:
        """Get the newest version of StatusBot available on Github."""
        # Get GitHub version string
        try:
            version = await get_github_file("version.txt", 3)
        except asyncio.exceptions.TimeoutError:
            await message.channel.send(
                "Connection timed out attempting to get version",
            )
            raise
        # Send message about it.
        await message.channel.send(f"Online version: {version}")
        # Make it tuple and return it
        return tuple(map(int, version.strip().split(".")))

    async def update(self, message: discord.message.Message) -> None:
        """Perform an update on this instance of StatusBot from GitHub."""
        timeout = 20
        if self.stopped.is_set():
            await message.channel.send(
                f"{__title__} is in the process of shutting down, "
                "canceling update.",
            )
            return
        configuration = self.get_dm_configuration()
        if "update-users" not in configuration:
            await message.channel.send(
                "No one has permission to run this command.",
            )
            return
        if message.author.id in configuration["update-users"]:
            with self.updating:
                await message.channel.send("Retrieving version from github...")
                # Send message of online version and get version tuple
                newvers = await self.online_vers(message)
                # Send message of current version and get version tuple
                curvers = await self.current_vers(message)
                # Figure out if we need update.
                if update.is_new_ver_higher(curvers, newvers):
                    # If we need update, get file list.
                    await message.channel.send("Retrieving file list...")
                    try:
                        response = await get_github_file("files.json")
                        paths = tuple(update.get_paths(json.loads(response)))
                    except Exception:  # pylint: disable=broad-except
                        # On failure, tell them we can't read file.
                        await message.channel.send(
                            "Could not read file list. Aborting update.",
                        )
                        log_active_exception()
                        return
                    # Get max amount of time this could take.
                    maxtime = format_time(timeout * len(paths))
                    # Stop everything if we are trying to shut down.
                    if self.stopped.is_set():
                        await message.channel.send(
                            f"{__title__} is in the process of shutting down, "
                            "canceling update.",
                        )
                        return
                    # Tell user number of files we are updating.
                    await message.channel.send(
                        f"{len(paths)} files will now be updated. "
                        f"Please wait. This may take up to {maxtime} at most.",
                    )
                    # Update said files.
                    rootdir = os.path.dirname(os.path.dirname(self.rootdir))
                    await update.update_files(
                        rootdir,
                        paths,
                        __title__,
                        __author__,
                        BRANCH,
                        timeout,
                    )
                    await message.channel.send(
                        "Done. Bot will need to be restarted to apply changes.",
                    )
                    return
                await message.channel.send("No update required.")
            return
        await message.channel.send(
            "You do not have permission to run this command.",
        )

    async def get_option__guild_option_autocomplete(
        self,
        interaction: discord.Interaction[StatusBot],
        current: str,
    ) -> list[discord.app_commands.Choice[str]]:
        """Autocomplete get option guild options."""
        if interaction.guild_id is None:
            return []
        configuration = self.get_guild_configuration(interaction.guild_id)
        valid = tuple(configuration.keys())
        return [
            discord.app_commands.Choice(name=option.title(), value=option)
            for option in valid
            if current.lower() in option.lower()
        ]

    @discord.app_commands.autocomplete(  # type: ignore [type-var]
        option=get_option__guild_option_autocomplete,
    )
    async def get_option__guild(
        self,
        message: discord.message.Message,
        option: str | None = None,
    ) -> None:
        """Get the value of the option given in this guild's configuration."""
        if message.guild is None:
            await message.channel.send(
                "Message guild is `None`, this is an error."
                f"Please report at {GITHUB_URL}/issues.",
            )
            raise ValueError("Message guild is None")
        configuration = self.get_guild_configuration(message.guild.id)
        valid = tuple(configuration.keys())

        if not valid:
            await message.channel.send("No options are set at this time.")
            return
        validops = get_valid_options(valid)

        if not option:
            await message.channel.send("Invalid option." + validops)
            return
        option = option.lower()
        if option not in valid:
            await message.channel.send("Invalid option." + validops)

        value = configuration.get(option)
        if not value and value != 0:
            await message.channel.send(f"Option `{option}` is not set.")
            return
        if isinstance(value, (list, tuple)):
            names = await self.replace_ids_w_names(value)
            value = combine_end(wrap_list_values(names, "`"))[1:-1]
        await message.channel.send(f"Value of option `{option}`: `{value}`.")

    async def get_option__dm_option_autocomplete(
        self,
        interaction: discord.Interaction[StatusBot],
        current: str,
    ) -> list[discord.app_commands.Choice[str]]:
        """Autocomplete get option guild options."""
        if interaction.guild_id is not None:
            return []
        configuration = self.get_dm_configuration()
        valid = []
        if interaction.user.id == OWNER_ID or (
            "set-option-users" in configuration
            and interaction.user.id in configuration["set-option-users"]
        ):
            valid += ["set-option-users", "update-users", "stop-users"]
        return [
            discord.app_commands.Choice(name=option.title(), value=option)
            for option in valid
            if current.lower() in option.lower()
        ]

    @discord.app_commands.autocomplete(  # type: ignore [type-var]
        option=get_option__dm_option_autocomplete,
    )
    async def get_option__dm(
        self,
        message: discord.message.Message,
        option: str | None = None,
    ) -> None:
        """Get the value of the option given in the configuration."""
        configuration = self.get_dm_configuration()
        valid = []
        if message.author.id == OWNER_ID or (
            "set-option-users" in configuration
            and message.author.id in configuration["set-option-users"]
        ):
            valid += ["set-option-users", "update-users", "stop-users"]

        if not valid:
            await message.channel.send("No options are set at this time.")
            return
        validops = get_valid_options(valid)

        if not option:
            await message.channel.send("No option given." + validops)
            return
        if not valid:
            await message.channel.send(
                "You do not have permission to view the values of any options.",
            )
            return
        option = option.lower()
        if option not in valid:
            await message.channel.send("Invalid option." + validops)
            return
        value = configuration.get(option)
        if not value and value != 0:
            await message.channel.send(
                f"Option `{option}` is not set.",
            )
            return
        if isinstance(value, (list, tuple)):
            names = await self.replace_ids_w_names(value)
            value = combine_end(wrap_list_values(names, "`"))[1:-1]
        await message.channel.send(
            f"Value of option `{option}`: `{value}`.",
        )
        return

    async def help_guild(self, message: discord.message.Message) -> None:
        """Get all valid options for guilds."""
        await send_command_list(self.gcommands, "Guild", message.channel)

    async def help_dm(self, message: discord.message.Message) -> None:
        """Get all valid options for direct messages."""
        await send_command_list(self.dcommands, "DM", message.channel)

    @discord.app_commands.rename(force_reset="force-reset")
    async def refresh(
        self,
        message: discord.message.Message,
        force_reset: bool = False,
    ) -> None:
        """Start server pinger or restart guild server pinger if force reset."""
        if message.guild is None:
            await message.channel.send(
                "Message guild is `None`, this is an error."
                f"Please report at {GITHUB_URL}/issues.",
            )
            raise ValueError("Message guild is None")

        if force_reset:
            configuration = self.get_guild_configuration(message.guild.id)
            allowed_users = set(configuration.get("force-refresh-users", []))
            allowed_users |= {OWNER_ID, message.guild.owner}
            if message.author.id not in allowed_users:
                await message.channel.send(
                    "No one except for the guild owner or people on the "
                    "`force-refresh-users` list are allowed "
                    "to force refreshes.",
                )
                force_reset = False
            else:
                await message.channel.send(
                    "Replacing the guild server pinger could take a bit, "
                    "we have to let the old one realize it should stop.",
                )
        await self.eval_guild(message.guild.id, force_reset)
        await message.channel.send("Guild has been re-evaluated.")

    @staticmethod
    def set_option__guild_valid_options(
        user_id: int,
        guild_admins: set[int],
        configuration: dict[str, Any],
    ) -> list[str]:
        """Return list of valid options to set for set option - guild."""
        valid = []
        # If message author is either bot owner or guild owner,
        if user_id in {OWNER_ID} | guild_admins:
            # give them access to everything
            valid += [
                "set-option-users",
                "address",
                "channel",
                "force-refresh-users",
            ]
        # If not, if set option users is defined in configuration,
        # and if message author is allowed to set options,
        elif (
            "set-option-users" in configuration
            and user_id in configuration["set-option-users"]
        ):
            # give them access to almost everything.
            valid += ["address", "channel", "force-refresh-users"]
        return valid

    async def set_option__guild_option_autocomplete(
        self,
        interaction: discord.Interaction[StatusBot],
        current: str,
    ) -> list[discord.app_commands.Choice[str]]:
        """Autocomplete set option guild options."""
        if interaction.guild_id is None or interaction.user.id is None:
            return []
        guild = self.get_guild(interaction.guild_id)
        if guild is None:
            return []
        configuration = self.get_guild_configuration(interaction.guild_id)

        admins: set[int] = set()
        if guild.owner is not None:
            admins.add(guild.owner.id)
        if (
            isinstance(interaction.user, discord.Member)
            and interaction.user.guild_permissions.administrator
        ):
            admins.add(interaction.user.id)

        valid = self.set_option__guild_valid_options(
            interaction.user.id,
            admins,
            configuration,
        )
        interaction.extras["option"] = [
            o for o in valid if current.replace(" ", "-").lower() in o.lower()
        ]
        return [
            discord.app_commands.Choice(
                name=option.replace("-", " ").title(),
                value=option,
            )
            for option in interaction.extras["option"]
        ]

    # async def set_option__guild_value_autocomplete(
    #     self,
    #     interaction: discord.Interaction[StatusBot],
    #     current: str
    # ) -> list[discord.app_commands.Choice[str]]:
    #     "Autocomplete set option guild options"
    #     options = interaction.extras.get(
    #         'option',
    #         [
    #             'set-option-users',
    #             'address', 'channel',
    #             'force-refresh-users'
    #         ]
    #     )
    #     print(f'{options = }')
    #     valid: set[str] = set()
    #     for option in options:
    #         if option in {'set-option-users', 'force-refresh-users'}:
    #             valid |= {'clear', '<user-id>', '<username>'}
    #         elif option == 'address':
    #             valid.add('<ip-address>')
    #         elif option == 'channel':
    #             valid.add('<channel-name>')
    #     return [
    #         discord.app_commands.Choice(
    #             name=option.replace('-', ' ').title(),
    #             value=option
    #         )
    #         for option in valid
    #         if current.replace(' ', '-').lower() in option.lower()
    #     ]

    # @commands.has_permissions(
    #     administrator=True, manage_messages=True, manage_roles=True
    # )
    @discord.app_commands.autocomplete(  # type: ignore[type-var]
        option=set_option__guild_option_autocomplete,
        # value=set_option__guild_value_autocomplete
    )
    async def set_option__guild(
        self,
        message: discord.message.Message,
        option: str,
        new_value: str | None = None,
    ) -> None:
        """Set a guild configuration option."""
        value: list[int] | list[str] | str | None = new_value
        if message.guild is None:
            await message.channel.send(
                "Message guild is `None`, this is an error. "
                f"Please report at {GITHUB_URL}/issues.",
            )
            raise ValueError("Message guild is None")
        configuration = self.get_guild_configuration(message.guild.id)

        admins: set[int] = set()
        if message.guild.owner is not None:
            admins.add(message.guild.owner.id)
        if (
            isinstance(message.author, discord.Member)
            and message.author.guild_permissions.administrator
        ):
            admins.add(message.author.id)

        valid = self.set_option__guild_valid_options(
            message.author.id,
            admins,
            configuration,
        )

        if not valid:
            await message.channel.send(
                "You do not have permission to set any options. "
                "If you feel this is a mistake, please contact server "
                "admin(s) and have them give you permission.",
            )
            return
        validops = get_valid_options(valid)

        if option not in valid:
            await message.channel.send("Invalid option." + validops)
            return

        if value is None:
            msg = f"Insufficient arguments for `{option}`."
            base = (
                "`clear`, a discord id, or the username of a new "
                "user to add to the "
            )
            arghelp = {
                "address": (
                    "Server address of a java edition minecraft server."
                ),
                "channel": (
                    "Name of the discord channel to "
                    "send join-leave messages to."
                ),
                "set-option-users": base + "set option permission list.",
                "force-refresh-users": base + "force reset permission list.",
            }
            msg += "\nArgument required: " + arghelp[option]
            await message.channel.send(msg)
            return

        if not value:
            await message.channel.send("Value to set must not be blank!")
            return

        if option == "channel":
            channelnames = [chan.name for chan in message.guild.text_channels]
            if value not in channelnames:
                await message.channel.send("Channel not found in this guild.")
                return
        elif option in {"set-option-users", "force-refresh-users"}:
            if str(value).lower() == "clear":
                value = []
            else:
                try:
                    id_value = int(str(value))
                except ValueError:
                    # DANGER
                    # if "#" not in value:
                    #     await message.channel.send(
                    #         "Username does not have discriminator (ex. #1234)."
                    #     )
                    #     return
                    member = message.guild.get_member_named(str(value))
                    if member is None:
                        await message.channel.send(
                            "User not found / User not in this guild.",
                        )
                        return
                    id_value = member.id
                # member = message.guild.get_member(value)
                member = message.guild.get_member(id_value)
                name: str | None = None
                if member is not None:
                    # member = self.get_user(value)
                    name = getattr(
                        member,
                        "name",
                        None,
                    )
                if name is None:
                    await message.channel.send(
                        "User not found / User not in this guild.",
                    )
                    return
                value = [id_value]
                if option in configuration:
                    if value[0] in configuration[option]:
                        await message.channel.send(
                            f"User `{name}` already in this list!",
                        )
                        return
                    value = configuration[option] + value
                assert value is not None
                await message.channel.send(
                    f"Adding user `{name}` (id `{value[-1]}`)",
                )
        configuration[option] = value
        self.write_guild_configuration(message.guild.id, configuration)
        await message.channel.send(
            f"Updated value of option `{option}` to `{value}`.",
        )
        force_reset = option in ("address", "channel")
        await self.refresh(message, force_reset)

    @staticmethod
    def set_option__dm_valid_options(
        user_id: int,
        configuration: dict[str, Any],
    ) -> list[str]:
        """Return list of valid options to set for set option - guild."""
        valid = []

        if user_id == OWNER_ID:
            valid += [
                "set-option-users",
                "update-users",
                "stop-users",
                "system-alert-users",
            ]
        elif (
            "set-option-users" in configuration
            and user_id in configuration["set-option-users"]
        ):
            valid += ["update-users", "stop-users", "system-alert-users"]

        return valid

    async def set_option__dm_option_autocomplete(
        self,
        interaction: discord.Interaction[StatusBot],
        current: str,
    ) -> list[discord.app_commands.Choice[str]]:
        """Autocomplete set option guild options."""
        if interaction.guild_id is not None or interaction.user.id is None:
            return []
        configuration = self.get_dm_configuration()

        valid = self.set_option__dm_valid_options(
            interaction.user.id,
            configuration,
        )
        interaction.extras["option"] = [
            o for o in valid if current.replace(" ", "-").lower() in o.lower()
        ]
        return [
            discord.app_commands.Choice(
                name=option.replace("-", " ").title(),
                value=option,
            )
            for option in interaction.extras["option"]
        ]

    @discord.app_commands.autocomplete(  # type: ignore[type-var]
        option=set_option__dm_option_autocomplete,
        # new_value=set_option__dm_value_autocomplete
    )
    async def set_option__dm(
        self,
        message: discord.message.Message,
        option: str | None = None,
        new_value: str | None = None,
    ) -> None:
        """Set a direct message configuration option."""
        configuration = self.get_dm_configuration()
        valid = self.set_option__dm_valid_options(
            message.author.id,
            configuration,
        )

        if not valid:
            await message.channel.send(
                "You do not have permission to set any options.",
            )
            return
        validops = get_valid_options(valid)

        if not option:
            await message.channel.send("Invalid option." + validops)
            return

        option = option.lower()

        if option not in valid:
            await message.channel.send("Invalid option." + validops)
            return

        if new_value is None:
            msg = f"Insufficient arguments for {option}."
            base = (
                "`clear`, a discord user id, or the username of a "
                "new user to add to the permission list of users who can "
            )
            arghelp = {
                "stop-users": base + "stop the bot.",
                "update-users": base + "update the bot.",
                "set-option-users": base
                + "change stop and update permissions.",
                "system-alert-users": base + "send system alerts.",
            }
            msg += "\nArgument required: " + arghelp[option]
            await message.channel.send(msg)
            return
        value: list[str] | list[int] | str | int = new_value
        if not value:
            await message.channel.send("Value to set must not be blank!")
            return
        if str(value).lower() == "clear":
            value = []
        else:
            try:
                value = int(str(value))
            except ValueError:
                # DANGER
                # if "#" not in args[1]:
                #     await message.channel.send(
                #         "Username does not have discriminator (ex. #1234)."
                #     )
                #    return
                member = await self.search_for_member_in_guilds(str(value))
                if member is None:
                    await message.channel.send("User not found.")
                    return
                value = member.id
            user = self.get_user(value)
            # # Slower but does not require members intent
            # user = self.fetch_user(value)
            if user is None:
                await message.channel.send("User not found.")
                return
            name = user.name
            value = [value]
            if option in configuration:
                if value[0] in configuration[option]:
                    await message.channel.send(
                        f"User `{name}` (id `{value[-1]}`) "
                        "already in this list!",
                    )
                    return
                value = configuration[option] + value
            assert isinstance(value, list)
            await message.channel.send(
                f"Adding user `{name}` (id `{value[-1]}`)",
            )
        configuration[option] = value
        self.write_dm_configuration(configuration)
        await message.channel.send(
            f"Updated value of option `{option}` to `{value}`.",
        )

    async def process_command_message(
        self,
        message: discord.message.Message,
        mode: str = "guild",
    ) -> None:
        """Process new command message. Calls self.command[command](message)."""
        # 1 if it's guild, 0 if direct message.
        midx = int(mode.lower() == "guild")

        if self.stopped.is_set() and midx:
            # Ignore if shutting down and in guild
            await message.channel.send(
                f"{__title__} is in the process of shutting down.",
            )
            return

        err = (
            " Please enter a valid command. Use "
            + "`{}help` to see valid commands."
        )
        # Format error text depending on if direct or guild message.
        err = err.format(("", self.prefix + " ")[midx])
        # Command list depends on direct or guild too.
        commands = (self.dcommands, self.gcommands)[midx]
        # Get content of message.
        content = message.content

        timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        name = ""
        with contextlib.suppress(Exception):
            name = message.author.name
        print(f"[{timestamp}] Command Message: {content!r} from {name!r}")

        # If no space in message
        if " " not in content:
            # If it's a guild message
            if midx:
                if content == self.prefix:
                    await message.channel.send("No command given." + err)
                return
            # Prefix doesn't have to be there in direct,
            # so add space so arguments work right.
            content += " "
        args = parse_args(content)

        # Get command. zeroth if direct, first if guild because of prefix.
        command = args[midx].lower()

        if command not in commands:
            if not midx and content.startswith(self.prefix):
                # if in a direct message and starts with our prefix,
                await message.channel.send(
                    "When you talk to me in DMs, there is no need to"
                    " start with my prefix for me to react!",
                )
                return
            # Otherwise, send error of no command.
            best = closest(command, tuple(commands))
            suggest = f"Did you mean `{best}`?"
            await message.channel.send(
                f"No valid command given. {suggest}{err}",
            )
            return

        command_func = commands[command]

        annotations = get_type_hints(command_func)
        params = {}
        for name, typeval in annotations.items():
            if name in {"return"}:
                continue
            if typeval in {discord.Message}:
                continue

            params[name] = typeval

        try:
            command_args = process_arguments(params, args[2:], message)
        except ValueError:
            names = combine_end(
                [
                    (
                        f"{k}"
                        if not isinstance(v, type)
                        else f"{k} ({v.__name__})"
                    )
                    for k, v in params.items()
                ],
            )
            await message.channel.send(
                f"Missing one or more arguments: {names}",
            )
            return

        # If command is valid, run it.
        await command_func(message, **command_args)

    # Intents.guilds
    async def on_guild_join(self, guild: discord.guild.Guild) -> None:
        """Evaluate guild."""
        msg = f"Guild gained: {guild.name} (id: {guild.id})"
        print(msg)
        append_file(self.logpath, "#" * 8 + msg + "#" * 8 + "\n")
        # await self.register_commands(guild)
        await self.eval_guild(guild.id, True)

    # Intents.guilds
    async def on_guild_remove(self, guild: discord.guild.Guild) -> None:
        """Remove configuration file for guild we are no longer in."""
        msg = f"""Guild lost: {guild.name} (id: {guild.id})
Deleting guild settings"""
        print(msg)
        append_file(self.logpath, "#" * 8 + msg + "#" * 8 + "\n")
        os.remove(self.get_guild_configuration_file(guild.id))
        gear = self.get_gear(str(guild.id))
        if gear is not None:
            if not gear.stopped:
                await gear.hault()
            self.remove_gear(str(guild.id))

    # Intents.dm_messages, Intents.guild_messages, Intents.messages
    async def on_message(self, message: discord.message.Message) -> None:
        """React to any new messages."""
        # Skip messages from ourselves.
        if message.author == self.user:
            return
        assert self.user is not None, "self.user should not be None"

        # If we can send message to person,
        if hasattr(message.channel, "send"):
            # If message is from a guild,
            if isinstance(message.guild, discord.guild.Guild):
                # If message starts with our prefix,
                args = parse_args(message.clean_content.lower())
                pfx = args[0] == self.prefix if len(args) >= 1 else False
                # of it starts with us being mentioned,
                mentioned = self.user.mentioned_in(message)
                # Skip messages mentioning @everyone or @here
                if mentioned and (
                    "@everyone" in message.content
                    or "@here" in message.content
                ):
                    mentioned = False
                if pfx or mentioned:
                    try:
                        # we are, in reality, the fastest typer in world. aw yep.
                        async with message.channel.typing():
                            # Process message as guild
                            await self.process_command_message(
                                message,
                                "guild",
                            )
                    except discord.errors.Forbidden:
                        # For some reason typing not allowed sometimes
                        await self.process_command_message(message, "guild")
                return
            # Otherwise, it's a direct message, so process it as one.
            async with message.channel.typing():
                await self.process_command_message(message, "dm")
        # can't send messages so skip.

    # Default, not affected by intents
    async def on_error(
        self,
        event: str,
        /,
        *args: Any,
        **kwargs: Any,
    ) -> None:  # pylint: disable=arguments-differ
        """Log error and continue."""
        if event == "on_message":
            print(f"Unhandled message: {args[0]}")
        extra = "Error Event:\n" + str(event) + "\n"
        extra += (
            "Error args:\n" + "\n".join(map(str, args)) + "\nError kwargs:\n"
        )
        extra += "\n".join(f"{key}:{val}" for key, val in kwargs.items())
        log_active_exception(self.logpath, extra=extra)

    # Default, not affected by intents
    async def close(self) -> None:
        """Tell guilds bot shutting down."""
        self.stopped.set()
        print("\nShutting down gears.")
        await gears.BaseBot.close(self)
        print("\nGears shut down...\n")

        # Telling guilds bot is shutting down.\n')
        async def tell_guild_shutdown(guild: discord.guild.Guild) -> None:
            channel = self.guess_guild_channel(guild.id)
            if channel is None:
                return
            with contextlib.suppress(discord.errors.Forbidden):
                await channel.send(
                    f"This instance of {__title__} is shutting down and presumably should be restarting shortly.",
                )
                await self.current_vers_channel(channel)

        coros = (tell_guild_shutdown(guild) for guild in self.guilds)
        await asyncio.gather(*coros)

        print("Waiting to acquire updating lock...\n")
        while self.updating.locked():
            print("Mid update, waiting for complete...")
            await asyncio.sleep(1)
        print("Closing...")
        await discord.Client.close(self)


def setup_bot(loop: asyncio.AbstractEventLoop) -> tuple[
    StatusBot,
    asyncio.Task[None],
]:
    """Return StatusBot run parts."""
    if TOKEN is None:
        raise RuntimeError(
            """No token set!
Either add ".env" file in bots folder with DISCORD_TOKEN=<token here> line,
or set DISCORD_TOKEN environment variable.""",
        )

    intents = discord.Intents(
        dm_messages=True,
        guild_messages=True,
        messages=True,
        guilds=True,
        guild_typing=True,
        members=True,
        message_content=True,
    )
    # 4867

    bot_run_task: asyncio.Task[None] | None = None

    bot = StatusBot(
        BOT_PREFIX,
        loop=loop,
        intents=intents,
    )

    bot_run_task = loop.create_task(bot.start(TOKEN))
    assert bot_run_task is not None

    return bot, bot_run_task


def run() -> None:
    """Run bot."""
    print("\nStarting bot...")

    loop = asyncio.new_event_loop()

    bot, bot_run_task = setup_bot(loop)

    try:
        loop.run_until_complete(bot_run_task)
    except KeyboardInterrupt:
        print("Received KeyboardInterrupt\nShutting down bot...")
        loop.run_until_complete(bot.close())
    finally:
        # cancel all lingering tasks
        loop.close()
        print("\nBot has been deactivated.")


if __name__ == "__main__":
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.")
    # logging.basicconfig(level=logging.INFO)
    run()
    # logging.shutdown()
