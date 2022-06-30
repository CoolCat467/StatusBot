#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# StatusBot for Discord

"Status Bot for Discord using Python 3"

# Programmed by CoolCat467

__title__ = 'StatusBot'
__author__ = 'CoolCat467'
__version__ = '0.4.4'
__ver_major__ = 0
__ver_minor__ = 4
__ver_patch__ = 4

from typing import Any, Awaitable, Callable, Dict, Final, Iterable, Optional, Set, Union

# https://discordpy.readthedocs.io/en/latest/index.html
# https://discord.com/developers

import os
import sys
import json
import math
import random
import traceback
import io
import asyncio
import concurrent.futures
from threading import Event, Lock
##import logging
import binascii
import base64

from dotenv import load_dotenv
import discord# type: ignore
##from discord.ext import tasks, commands

# Update talks to GitHub
import update

# server_status is basically fork of
# https://github.com/Dinnerbone/mcstatus
# with some slight modifications to make it better,
# especially asynchronous stuff.
from status import server_status as mc

# Gears is basically like discord's Cogs, but
# by me.
import gears

# Acquire token.
# Looks for file named ".env",
# file line 1 is "# .env",
# file line 2 is "DISCORD_TOKEN=XXXXX"
load_dotenv()
TOKEN: Final = os.getenv('DISCORD_TOKEN')

BOT_PREFIX = '!status'
OWNER_ID = 344282497103691777
# Branch is branch of GitHub repository to update from
BRANCH = 'master'

# Text globals
AZUP = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
AZLOW = AZUP.lower()
NUMS = '0123456789'


def write_file(filename: str, data: str) -> None:
    "Write data to file <filename>."
    filename = os.path.abspath(filename)
    with open(filename, 'w', encoding='utf-8') as wfile:
        wfile.write(data)
        wfile.close()

def append_file(filename: str, data: str) -> None:
    "Add data to file <filename>."
    filename = os.path.abspath(filename)
    if os.path.exists(filename):
        with open(filename, 'a', encoding='utf-8') as wfile:
            wfile.write(data)
            wfile.close()
    else:
        write_file(filename, data)

def read_file(filename: str) -> Union[str, None]:
    "Read data from file <filename>. Return None if file does not exist."
    filename = os.path.abspath(filename)
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as rfile:
            data = rfile.read()
            rfile.close()
        return data
    return None

def read_json(filename: str) -> Union[dict, None]:
    "Return json loads of filename read. Returns None if filename not exists."
    filename = os.path.abspath(filename)
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as rfile:
            try:
                data = json.load(rfile)
            except json.decoder.JSONDecodeError:
                return None
            finally:
                rfile.close()
        return data
    return None

def write_json(filename: str, dictionary: dict, indent: int=2) -> None:
    "Write dictionary as json to filename."
    filename = os.path.abspath(filename)
    with open(filename, 'w', encoding='utf-8') as wfile:
        try:
            json.dump(dictionary, wfile, indent=indent)
        finally:
            wfile.close()

def split_time(seconds: int) -> list[int]:
    "Split time into decades, years, months, weeks, days, hours, minutes, and seconds."
    seconds = int(seconds)
    def mod_time(sec: int, num: int) -> tuple[int, int]:
        "Return number of times sec divides equally by number, then remainder."
        smod = sec % num
        return int((sec - smod) // num), smod
    # pylint: disable=wrong-spelling-in-comment
    ##values = (1, 60, 60, 24, 7, 365/12/7, 12, 10, 10, 10, 1000, 10, 10, 5)
    ##mults = {0:values[0]}
    ##for i in range(len(values)):
    ##    mults[i+1] = round(mults[i] * values[i])
    ##divs = list(reversed(mults.values()))[:-1]
    divs = (15768000000000000,
            3153600000000000,
            315360000000000,
            31536000000000,
            31536000000,
            3153600000,
            315360000,
            31536000,
            2628000,
            604800,
            86400,
            3600,
            60,
            1)
    ret = []
    for num in divs:
        edivs, seconds = mod_time(seconds, num)
        ret.append(edivs)
    return ret

def combine_and(data: list) -> str:
    "Join values of text, and have 'and' with the last one properly."
    data = list(data)
    if len(data) >= 2:
        data[-1] = f'and {data[-1]}'
    if len(data) > 2:
        return ', '.join(data)
    return ' '.join(data)

def format_time(seconds: int, single_title_allowed: bool=False) -> str:
    "Returns time using the output of split_time."
    times = ('eons', 'eras', 'epochs', 'ages', 'millenniums',
             'centuries', 'decades', 'years', 'months', 'weeks',
             'days', 'hours', 'minutes', 'seconds')
    single = [i[:-1] for i in times]
    single[5] = 'century'
    zip_idx_values = [(i, v) for i, v in enumerate(split_time(seconds)) if v]
    if single_title_allowed:
        if len(zip_idx_values) == 1:
            index, value = zip_idx_values[0]
            if value == 1:
                return f'a {single[index]}'
    data = []
    for index, value in zip_idx_values:
        title = single[index] if abs(value) < 2 else times[index]
        data.append(f'{value} {title}')
    return combine_and(data)

def except_chars(text: str, valid: str=AZUP+AZLOW+NUMS+'.:-') -> str:
    "Return every character in text that is also in valid string."
    return ''.join(i for i in text if i in valid)

def parse_args(string: str, ignore: int=0, sep: str=' ') -> list[str]:
    "Return a list of arguments by splitting string by separation, omitting first ignore arguments."
    return string.split(sep)[ignore:]

def wrap_list_values(items: Iterable[str], wrap: str='`') -> list[str]:
    "Wrap all items in list of strings with wrap. Ex. ['cat'] -> ['`cat`']"
    return [f'{wrap}{item}{wrap}' for item in items]

def log_active_exception(logpath: str, extra: str=None) -> None:
    "Log active exception."
    # Get values from exc_info
    values = sys.exc_info()
    # Get error message.
    msg = '#'*16+'\n'
    if not extra is None:
        msg += f'{extra}\n'
    msg += 'Exception class:\n'+str(values[0])+'\n'
    msg += 'Exception text:\n'+str(values[1])+'\n'

    with io.StringIO() as yes_totaly_a_file:
        traceback.print_exception(None,
                                  value=values[1],
                                  tb=values[2],
                                  limit=None,
                                  file=yes_totaly_a_file,
                                  chain=True)
        msg += '\n'+yes_totaly_a_file.getvalue()+'\n'+'#'*16+'\n'
    print(msg)
    append_file(logpath, msg)

async def send_over_2000(send_func: Callable[[str], Awaitable[None]],
                         text: str,
                         header: str='',
                         wrap_with: str='',
                         replace_existing_wrap: bool=True) -> None:
    "Use send_func to send text in segments over 2000 characters by "\
    "splitting it into multiple messages."
    send = str(text)
    add_aloc = len(header)
    if wrap_with:
        if replace_existing_wrap:
            send = send.replace(wrap_with, '')
        add_aloc += int(len(wrap_with) * 2)
    parts = []
    count = len(send)+add_aloc
    if count > 2000:
        last = 0
        for i in range(0, len(send), 2000-add_aloc):
            parts.append(send[last:i])
            last = i
        del parts[0]
        if last < count:
            parts.append(send[last:])
    else:
        parts.append(send)
    parts = [header+part for part in parts]
    if wrap_with:
        parts = wrap_list_values(parts, wrap_with)
    # pylint: disable=wrong-spelling-in-comment
    # This would be great for asyncio.gather, but
    # I'm pretty sure that will throw off call order,
    # and it's quite important that everything stays in order.
##    coros = [send_func(part) for part in parts]
##    await asyncio.gather(*coros)
    for part in parts:
        await send_func(part)

async def get_github_file(path: str, timeout: int=10) -> str:
    "Return text from GitHub file in this project decoded as utf-8"
    file = await update.get_file(__title__, path, __author__, BRANCH, timeout)
    return file.decode('utf-8')

class PingState(gears.AsyncState):
    "State where we ping server."
    __slots__ = 'failed', 'exit_ex'
    machine: 'GuildServerPinger'
    def __init__(self) -> None:
        super().__init__('ping')
        self.failed = False
        self.exit_ex: Optional[str] = None

    async def entry_actions(self) -> None:
        "Reset failed to false and exception to None."
        self.failed = False
        self.exit_ex = None
        self.machine.last_delay = math.inf
        self.machine.last_online = set()

    async def handle_sample(self, players: Set[str]) -> None:
        "Handle change in players by players sample."
        # If different players,
        if players == self.machine.last_online:
            return
        # Find difference in players.
        joined = tuple(players.difference(self.machine.last_online))
        left = tuple(self.machine.last_online.difference(players))

        def users_mesg(action: str, users: Iterable[str]) -> str:
            "Returns [{action}]: {users}"
            text = f'[{action}]:\n'
            text += combine_and(wrap_list_values(users, '`'))
            return text
        # Collect left and joined messages.
        message = ''
        if left:
            message = users_mesg('Left', left)
        if joined:
            if message:
                message += '\n'
            message += users_mesg('Joined', joined)
        # Send message to guild channel.
        if message:
            await send_over_2000(self.machine.channel.send, message)

    async def handle_count(self, online: int) -> None:
        "Handle change in players by online count."
        # Otherwise, server with player sample disabled
        # and can only tell number of left/joined
        if online == self.machine.last_online_count:
            # If same, no need
            return
        diff = online - self.machine.last_online_count
        if diff == 0:
            return
        player = 'player' if diff == 1 else 'players'
        if diff > 0:
            await self.machine.channel.send(f'[Joined]: {diff} {player}')
        else:
            await self.machine.channel.send(f'[Left]: {-diff} {player}')

    async def do_actions(self) -> None:
        "Ping server. If failure, self.failed = True and if exceptions, save."
        try:
            json_data, ping = await self.machine.server.async_status()
        except Exception as ex:# pylint: disable=broad-except
            self.exit_ex = f'`A {type(ex).__name__} Exception Has Occored'
            if ex.args:
                sargs = list(map(str, ex.args))
                self.exit_ex += ': '+combine_and(wrap_list_values(sargs, '"'))
            self.exit_ex += '`'
            self.failed = True
##            print(self.exit_ex)
            # No need to record detailed errors for timeouts.
            ignore = (concurrent.futures.TimeoutError,
                      asyncio.exceptions.TimeoutError,
                      ConnectionRefusedError,
                      IOError)
            if not isinstance(ex, ignore):
                log_active_exception(self.machine.bot.logpath)
            return
        # If success, get players.
        self.machine.last_json = json_data
        self.machine.last_delay = ping

        players: Set[str] = set()
        online = 0

        if not 'players' in json_data:
            # Update last ping.
            self.machine.last_online = players
            return

        if 'online' in json_data['players']:
            online = json_data['players']['online']
        if 'sample' in json_data['players']:
            for player in json_data['players']['sample']:
                if 'name' in player:
                    players.add(player['name'])

        if len(players) == 0 and online:
            await self.handle_count(online)
            self.machine.last_online_count = online
        else:
            await self.handle_sample(players)
            # Update last ping.
            self.machine.last_online = players
        self.machine.last_online_count = max(online, len(players))

    async def check_conditions(self) -> Optional[str]:
        "If there was failure to connect to server, await restart."
        if self.failed:
            return 'await_restart'

    async def exit_actions(self) -> None:
        "When exiting, if we collected an exception, send it to channel."
        if not self.exit_ex is None:
            await self.machine.channel.send(self.exit_ex)

class WaitRestartState(gears.AsyncState):
    "State where we wait for server to restart."
    __slots__ = 'ignore_ticks', 'success', 'ticks', 'ping'
    machine: 'GuildServerPinger'
    def __init__(self, ignore_ticks: int) -> None:
        super().__init__('await_restart')
        self.ignore_ticks = ignore_ticks
        self.success = False
        self.ticks = 0
        self.ping: Union[int, float] = 0

    async def entry_actions(self) -> None:
        "Reset failed and say connection lost."
        extra = ''
        if not self.machine.last_delay in {math.inf, 0}:
            extra = f' Last successful ping latency was `{self.machine.last_delay}ms`'
        await self.machine.channel.send('Connection to server has been lost.'+extra)
        self.success = False
        self.ticks = 0
        self.ping = 0

    async def attempt_contact(self) -> bool:
        "Attempt to talk to server."
        try:
            self.ping = await self.machine.server.async_ping()
        except Exception:# pylint: disable=broad-except
            pass
        else:
            return True
        return False

    async def do_actions(self) -> None:
        "Every once and a while try to talk to server again."
        self.ticks = (self.ticks + 1) % self.ignore_ticks

        if self.ticks == 0:
            self.success = await self.attempt_contact()

    async def check_conditions(self) -> Optional[str]:
        "If contact attempt was successfully, switch back to ping."
        if self.success:
            return 'ping'

    async def exit_actions(self) -> None:
        if self.success:
            await self.machine.channel.send(
            f'Connection to server re-established with a ping of `{self.ping}ms`.')
        else:
            await self.machine.channel.send(
            'Could not re-establish connection to server.')

class GuildServerPinger(gears.StateTimer):
    "Server ping machine for guild."
    __slots__ = ('guildid', 'server', 'last_online',
                 'last_json', 'last_delay',
                 'last_online_count', 'last_online',
                 'channel')
    tickspeed: int = 60
    waitticks: int = 5
    def __init__(self, bot: 'StatusBot', guildid: int) -> None:
        "Needs bot we work for, and id of guild we are pinging the server for."
        self.guildid = guildid
        super().__init__(bot, str(self.guildid), self.tickspeed)
        self.bot: 'StatusBot'
        self.server = mc.Server('')
        self.last_json: Dict[str, Any] = {}
        self.last_delay: Union[int, float] = 0
        self.last_online: Set[str] = set()
        self.last_online_count: int = 0
        self.channel: discord.abc.Messageable

        self.add_state(PingState())
        self.add_state(WaitRestartState(self.waitticks))

    @property
    def wait_time(self) -> int:
        "Total wait time when in await_restart state."
        return self.tickspeed * self.waitticks

    async def initialize_state(self) -> None:
        "Set state to ping."
        await self.set_state('ping')

    async def start(self) -> None:
        "If configuration is good, run."
        configuration = self.bot.get_guild_configuration(self.guildid)
        self.channel = self.bot.guess_guild_channel(self.guildid)
        if 'address' in configuration:
            self.server = mc.Server.lookup(configuration['address'])
            try:
                await super().start()
            except Exception:# pylint: disable=broad-except
                log_active_exception(self.bot.logpath)
            finally:
                await self.channel.send('Server pinger stopped.')
        else:
            await self.channel.send('No address for this guild defined, pinger not started.')

def get_valid_options(valid: Iterable[str], wrap: str='`') -> str:
    "Return string of ' Valid options are: {valid}' but with pretty formatting."
    validops = combine_and(wrap_list_values(valid, wrap))
    return f' Valid options are: {validops}.'

async def send_command_list(commands: dict[str, Any],
                            name: str,
                            channel: discord.abc.Messageable) -> None:
    "Send message on channel telling user about all valid name commands."
    sort = sorted(commands.keys(), reverse=True)
    text = f"{__title__}'s Valid {name} Commands:"
    await channel.send(text)
    await send_over_2000(channel.send, '\n'.join(wrap_list_values(sort, '`')))

class StatusBot(discord.Client, gears.BaseBot):# pylint: disable=too-many-public-methods,too-many-instance-attributes
    "StatusBot needs prefix, event loop, and any arguments to pass to discord.Client."
    def __init__(self,
                 prefix: str,
                 loop: asyncio.AbstractEventLoop,
                 *args,
                 **kwargs) -> None:
        self.loop = loop
        if 'loop' in kwargs:
            del kwargs['loop']
        discord.Client.__init__(self, *args, loop=self.loop, **kwargs)
        self.stopped = Event()
        self.updating = Lock()
        self.prefix = prefix
        self.rootdir = os.path.split(os.path.abspath(__file__))[0]
        self.logpath = os.path.join(self.rootdir, 'log.txt')
        self.gcommands: Dict[str, Callable[[discord.message.Message], Awaitable[None]]] = {
            'currentversion': self.getcurrentvers,
            'onlineversion': self.getonlinevers,
            'getmyid': self.getmyid,
            'getjson': self.getjson,
            'getfavicon': self.getfavicon,
            'getonline': self.getonline,
            'getping': self.getping,
            'refresh': self.refresh,
            'setoption': self.setoption_guild,
            'getoption': self.getoption_guild,
            'help': self.help_guild
        }
        self.dcommands: Dict[str, Callable[[discord.message.Message], Awaitable[None]]] = {
            'currentversion': self.getcurrentvers,
            'onlineversion': self.getonlinevers,
            'getmyid': self.getmyid,
            'stop': self.stop,
            'update': self.update,
            'setoption': self.setoption_dm,
            'getoption': self.getoption_dm,
            'help': self.help_dm
        }
        gears.BaseBot.__init__(self, self.loop)

    def __repr__(self) -> str:
##        up = self.__class__.__weakref__.__qualname__.split('.')[0]
        return f'<{self.__class__.__name__} Object>'# ({up} subclass)>'

    @property
    def gear_close(self) -> bool:
        "Return True if gears should close."
        return self.stopped.is_set() or self.is_closed()

    async def wait_ready(self) -> None:
        "Define wait for gears BaseBot"
        await self.wait_until_ready()

    def get_guild_configuration_file(self, guildid: int) -> str:
        "Return the path to the configuration json file for a certain guild id."
        return os.path.join(self.rootdir, 'config', 'guilds', str(guildid)+'.json')

    def get_dm_configuration_file(self) -> str:
        "Return the path to the configuration json file for all direct messages."
        return os.path.join(self.rootdir, 'config', 'dms.json')

    def get_guild_configuration(self, guildid: int) -> dict:
        "Return a dictionary from the json read from guild configuration file."
        guildfile = self.get_guild_configuration_file(guildid)
        guildconfiguration = read_json(guildfile)
        if guildconfiguration is None:
            # Guild does not have configuration
            # Therefore, create file for them
            write_file(guildfile, '{}')
            guildconfiguration = {}
        return guildconfiguration

    def get_dm_configuration(self) -> dict:
        "Return a dictionary from the json read from the direct messages configuration file."
        dmfile = self.get_dm_configuration_file()
        dmconfiguration = read_json(dmfile)
        if dmconfiguration is None:
            write_file(dmfile, '{}')
            dmconfiguration = {}
        return dmconfiguration

    def write_guild_configuration(self, guildid: int, configuration: dict) -> None:
        "Write guild configuration file from configuration dictionary."
        guildfile = self.get_guild_configuration_file(guildid)
        write_file(guildfile, json.dumps(configuration, indent=2))

    def write_dm_configuration(self, configuration: dict) -> None:
        "Write direct message configuration file from configuration dictionary."
        dmfile = self.get_dm_configuration_file()
        write_file(dmfile, json.dumps(configuration, indent=2))

    def guess_guild_channel(self, gid: int) -> discord.abc.Messageable:
        "Guess guild channel and return channel."
        guild = self.get_guild(gid)
        configuration = self.get_guild_configuration(gid)
        valid = [chan.name for chan in guild.text_channels]
        if 'channel' in configuration:
            channelname = configuration['channel']
            if channelname in valid:
                channel = discord.utils.get(guild.text_channels, name=channelname)
                return channel
        expect = [cname for cname in valid if 'bot' in cname.lower()]
        expect += ['general']
        for channel in guild.text_channels:
            if channel.name in expect:
                return channel
        return random.choice(guild.text_channels)

    async def search_for_member_in_guilds(self, username: str) -> discord.user.User:
        "Search for member in all guilds we connected to. Return None on failure."
        members = (guild.get_member_named(username) for guild in self.guilds)
        for member in members:
            if not member is None:
                return member

    async def add_guild_pinger(self, gid: int, force_reset: bool=False) -> str:
        "Create ping machine for guild if not exists. Return 'started', 'restarted', or 'none'."
        if str(gid) not in self.gears:
            self.add_gear(GuildServerPinger(self, gid))
            return 'started'
        if force_reset or not self.gears[str(gid)].running:
            if not self.gears[str(gid)].stopped:
                await self.gears[str(gid)].hault()
            self.remove_gear(str(gid))
            self.add_gear(GuildServerPinger(self, gid))
            return 'restarted'
        return 'none'

    async def eval_guild(self, guildid: int, force_reset: bool=False) -> int:
        "(Re)Start guild machine if able. Otherwise tell them to change settings."
        guildconfiguration = self.get_guild_configuration(guildid)
        channel = self.guess_guild_channel(guildid)
        if not 'channel' in guildconfiguration:
            await channel.send('This is where I will post leave-join messages '\
                               'until an admin sets my `channel` option.')
        if 'address' in guildconfiguration:
            action = await self.add_guild_pinger(guildid, force_reset)
            if action != 'none':
                await channel.send(f'Server pinger {action}.')
            else:
                await channel.send('No action taken.')
        else:
            await channel.send('Server address not set, pinger not started. '\
                               f'Please set it with `{self.prefix} setoption address <address>`.')
        return guildid

    async def eval_guilds(self, force_reset: bool=False) -> list:
        "Evaluate all guilds. Return list of guild ids evaluated."
        coros = (self.eval_guild(guild.id, force_reset) for guild in self.guilds)
        return await asyncio.gather(*coros)

    # Default, not affected by intents.
    async def on_ready(self) -> None:
        "Print information about bot and evaluate all guilds."
        print(f'{self.user} has connected to Discord!')
        print(f'Prefix: {self.prefix}')
        print(f'Intents: {self.intents}')
        print(f'Root Dir: {self.rootdir}')

        configurationdir = os.path.join(self.rootdir, 'config')
        if not os.path.exists(configurationdir):
            os.mkdir(configurationdir)
        guilddir = os.path.join(configurationdir, 'guilds')
        if not os.path.exists(guilddir):
            os.mkdir(guilddir)
        favicondir = os.path.join(self.rootdir, 'favicon')
        if not os.path.exists(favicondir):
            os.mkdir(favicondir)

        print(f'\n{self.user} is connected to the following guilds:\n')
        guildnames = []
        for guild in self.guilds:
            guildnames.append(f'{guild.name} (id: {guild.id})')
        spaces = max(len(name) for name in guildnames)
        print('\n'+'\n'.join(name.rjust(spaces) for name in guildnames)+'\n')
        ids = await self.eval_guilds(True)
        print('Guilds evaluated:\n'+'\n'.join([str(x) for x in ids])+'\n')
        act = discord.Activity(type=discord.ActivityType.watching, name=f'for {self.prefix}')
        await self.change_presence(status=discord.Status.online, activity=act)
        return

    async def get_user_name(self,
                            uid: int,
                            getmember: Callable[[int], discord.abc.Messageable]=None
                            )-> Union[str, None]:
        "Return the name of user with id given."
        if getmember is None:
            getmember = self.get_user
        member = getmember(uid)
        if member is None:
            return member
        return f'{member.name}#{member.discriminator}'

    async def replace_ids_w_names(self, names: Iterable[Union[str, int]]) -> list[str]:
        "Replace user ids (integers) with usernames in lists. Returns list of strings."
        replaced = []
        for item in names:
            if isinstance(item, int):
                username = await self.get_user_name(item)
                if not username is None:
                    replaced.append(f'{username} (id. {item})')
                    continue
            replaced.append(str(item))
        return replaced

    async def getmyid(self, message: discord.message.Message) -> None:
        "Tell the author of the message their user id."
        await message.channel.send(f'Your user id is `{message.author.id}`.')

    async def save_favicon(self, guildid: int) -> None:
        "Save favicon image to favicon folder for this guild's server"
        if guildid not in self.gears:
            return
        pinger: GuildServerPinger = self.gears[str(guildid)]
        if pinger.active_state is None or pinger.active_state.name != 'ping' or not 'favicon' in pinger.last_json:
            return
        favicon_data = pinger.last_json['favicon']
        if not favicon_data.startswith('data:image/png;base64,'):
            return
        favicon_data = favicon_data.split(',')[1]
        try:
            data = base64.b64decode(favicon_data)
            filename = os.path.abspath(
                os.path.join(self.rootdir, 'favicon', f'{guildid}.png')
            )
            with open(filename, mode='wb') as favicon_file:
                favicon_file.write(data)
                favicon_file.close()
        except binascii.Error:
            print('Encountered error decoding base64 string for favicon.')

    async def getfavicon(self, message: discord.message.Message) -> None:
        "Post favicon for server"
        await self.save_favicon(message.guild.id)
        filename = os.path.join(self.rootdir, 'favicon', f'{message.guild.id}.png')
        if not os.path.exists(filename):
            await message.channel.send('Something went wrong attempting to get favicon.')
            return
        with open(filename, 'rb') as file_handle:
            file = discord.File(file_handle, filename=filename)
            await message.channel.send(file=file)
            file_handle.close()

    async def getjson(self, message: discord.message.Message) -> None:
        "Tell the author of the message the last json from server machine."
        if str(message.guild.id) in self.gears:
            pinger: GuildServerPinger = self.get_gear(str(message.guild.id))
            if pinger.active_state is None:
                await message.channel.send('Server pinger is not active for this guild. '+
                                           'Use command `refresh` to restart.')
                return
            if pinger.active_state.name == 'ping':
                lastdict = pinger.last_json
                if 'favicon' in lastdict:
                    lastdict['favicon'] = '<base64 image data>'
                msg = json.dumps(lastdict, sort_keys=True, indent=2)
                await message.channel.send('Last received json message:')
                await send_over_2000(message.channel.send, msg, 'json\n', '```', False)
                return
            delay = format_time(pinger.wait_time)
            await message.channel.send(
                f'Cannot connect to server at this time, try again in {delay}.')
            return
        await message.channel.send('Server pinger is not running for this guild. '\
                                   'Use command `refresh` to restart.')

    async def getping(self, message: discord.message.Message) -> None:
        "Tell the author of the message the connection latency to the guild's server."
        if str(message.guild.id) in self.gears:
            pinger: GuildServerPinger = self.get_gear(str(message.guild.id))
            if pinger.active_state is None:
                await message.channel.send('Server pinger is not active for this guild. '+
                                           'Use command `refresh` to restart.')
                return
            if pinger.active_state.name == 'ping':
                msg = f'`{pinger.last_delay}ms`'
                await message.channel.send(
                    f"{__title__}'s last received latency to defined guild server:\n"+msg)
                return None
            delay = format_time(pinger.wait_time)
            await message.channel.send(
                f'Cannot connect to server at this time, try again in {delay}.')
            return
        await message.channel.send('Server pinger is not running for this guild. '\
                                   'Use command `refresh` to restart.')

    async def getonline(self, message: discord.message.Message) -> None:
        "Tell author of the message the usernames of the players connected to the guild's server."
        if str(message.guild.id) in self.gears:
            pinger: GuildServerPinger = self.get_gear(str(message.guild.id))
            if pinger.active_state is None:
                await message.channel.send('Server pinger is not active for this guild. '\
                                           'Use command `refresh` to restart.')
                return
            if pinger.active_state.name == 'ping':
                players = list(pinger.last_online)
                if players:
                    player_text = combine_and(wrap_list_values(players, '`'))
                    await message.channel.send('Players online in last received sample:')
                    await send_over_2000(message.channel.send, player_text)
                elif pinger.last_online_count:
                    await message.channel.send(f'There were `{pinger.last_online_count}` '\
                                               'players online in last received message.')
                else:
                    await message.channel.send('No players were online in the last received sample.')
                return
            delay = format_time(pinger.wait_time)
            await message.channel.send(
                f'Cannot connect to server at this time, try again in {delay}.')
            return
        await message.channel.send('Server pinger is not running for this guild. '\
                                   'Use command `refresh` to restart.')

    async def stop(self, message: discord.message.Message) -> None:
        "Stop this bot. Sends stop message."
        configuration = self.get_dm_configuration()
        if not 'stopusers' in configuration:
            await message.channel.send('No one has permission to run this command.')
            return

        if message.author.id in configuration['stopusers']:
            await message.channel.send('Stopping...')
            # Set stopped event
            self.stopped.set()
            def close_bot() -> None:
                self.loop.create_task(self.close())
            self.loop.call_later(3, close_bot)
            return
        await message.channel.send('You do not have permission to run this command.')

    async def getcurrentvers(self, message: discord.message.Message) -> tuple[int, ...]:
        "Get current version, tell user in message.channel, and return that version as tuple."
        proj_root = os.path.split(self.rootdir)[0]
        version = read_file(os.path.join(proj_root, 'version.txt'))
        await message.channel.send(f'Current version: {version}')
        if not version:
            return (__ver_major__, __ver_minor__, __ver_patch__)
        return tuple(map(int, version.strip().split('.')))

    async def getonlinevers(self, message: discord.message.Message) -> tuple[int, ...]:
        "Get online version, tell user in message.channel, and return said version as tuple."
        # Get GitHub version string
        version = await get_github_file('version.txt')
        # Send message about it.
        await message.channel.send(f'Online version: {version}')
        # Make it tuple and return it
        return tuple(map(int, version.strip().split('.')))

    async def update(self, message: discord.message.Message, timeout: int=20) -> None:
        "Preform update from GitHub."
        if self.stopped.is_set():
            await message.channel.send(
                f'{__title__} is in the process of shutting down, canceling update.')
            return
        configuration = self.get_dm_configuration()
        if not 'updateusers' in configuration:
            await message.channel.send('No one has permission to run this command.')
            return
        if message.author.id in configuration['updateusers']:
            with self.updating:
                await message.channel.send('Retrieving version from github...')
                # Send message of online version and get version tuple
                newvers = await self.getonlinevers(message)
                # Send message of current version and get version tuple
                curvers = await self.getcurrentvers(message)
                # Figure out if we need update.
                if update.is_new_ver_higher(curvers, newvers):
                    # If we need update, get file list.
                    await message.channel.send('Retrieving file list...')
                    try:
                        response = await get_github_file('files.json')
                        paths = tuple(update.get_paths(json.loads(response)))
                    except Exception:# pylint: disable=broad-except
                        # On failure, tell them we can't read file.
                        await message.channel.send('Could not read file list. Aborting update.')
                        return
                    # Get max amount of time this could take.
                    maxtime = format_time(timeout*len(paths))
                    # Stop everything if we are trying to shut down.
                    if self.stopped.is_set():
                        await message.channel.send(
                            f'{__title__} is in the process of shutting down, canceling update.')
                        return
                    # Tell user number of files we are updating.
                    await message.channel.send(f'{len(paths)} files will now be updated. '\
                                               f'Please wait. This may take up to {maxtime} at most.')
                    # Update said files.
                    rootdir = os.path.split(self.rootdir)[0]
                    await update.update_files(rootdir, paths, __title__, __author__, BRANCH, timeout)
                    await message.channel.send('Done. Bot will need to be restarted to apply changes.')
                    return
                await message.channel.send('No update required.')
            return
        await message.channel.send('You do not have permission to run this command.')

    async def getoption_guild(self, message: discord.message.Message) -> None:
        "Send message with value of option given in this guild's configuration."
        args = parse_args(message.content, 2)
        configuration = self.get_guild_configuration(message.guild.id)
        valid = tuple(configuration.keys())

        if not valid:
            await message.channel.send('No options are set at this time.')
            return
        validops = get_valid_options(valid)

        if not args:
            await message.channel.send('Invalid option.'+validops)
            return
        option = args[0].lower()
        if option in valid:
            value = configuration[option]
            if not value and value != 0:
                await message.channel.send(f'Option `{option}` is not set.')
                return
            if isinstance(value, (list, tuple)):
                names = await self.replace_ids_w_names(value)
                value = combine_and(wrap_list_values(names, '`'))[1:-1]
            await message.channel.send(f'Value of option `{option}`: `{value}`.')
            return
        await message.channel.send('Invalid option.'+validops)

    async def getoption_dm(self, message: discord.message.Message) -> None:
        "Send message with value of option given in the direct message configuration."
        args = parse_args(message.content, 1)
        configuration = self.get_dm_configuration()
        valid = []
        if message.author.id == OWNER_ID:
            valid += ['setoptionusers', 'updateusers', 'stopusers']
        elif 'setoptionusers' in configuration:
            if message.author.id in configuration['setoptionusers']:
                valid += ['setoptionusers', 'updateusers', 'stopusers']

        if not valid:
            await message.channel.send('No options are set at this time.')
            return
        validops = get_valid_options(valid)

        if len(args) == 0:
            await message.channel.send('No option given.'+validops)
            return
        if valid:
            option = args[0].lower()
            if option in valid:
                value = configuration[option]
                if not value and value != 0:
                    await message.channel.send(f'Option `{option}` is not set.')
                    return
                if isinstance(value, (list, tuple)):
                    names = await self.replace_ids_w_names(value)
                    value = combine_and(wrap_list_values(names, '`'))[1:-1]
                await message.channel.send(f'Value of option `{option}`: `{value}`.')
                return
            await message.channel.send('Invalid option.'+validops)
            return
        await message.channel.send('You do not have permission to view the values of any options.')

    async def help_guild(self, message: discord.message.Message) -> None:
        "Send a message on message.channel telling user about all valid options."
        await send_command_list(self.gcommands, 'Guild', message.channel)

    async def help_dm(self, message: discord.message.Message) -> None:
        "Send a message on message.channel telling user about all valid options."
        await send_command_list(self.dcommands, 'DM', message.channel)

    async def refresh(self, message: discord.message.Message, force_reset: bool=False) -> None:
        "Re-evaluate guild, then tell them it happened."
        if not force_reset:
            auid = message.author.id
            args = parse_args(message.clean_content)
            if len(args) > 2:
                configuration = self.get_guild_configuration(message.guild.id)
                if args and args[2].lower() == 'force':
                    if auid in {OWNER_ID, message.guild.owner}:
                        force_reset = True
                    elif 'forcerefreshusers' in configuration:
                        if auid in configuration['forcerefreshusers']:
                            force_reset = True
                    else:
                        await message.channel.send(
                            'No one except for the guild owner is allowed to force refreshes'
                        )

        if force_reset:
            await message.channel.send('Replacing the guild server pinger could take a bit, '\
                                       'we have to let the old one realize it should stop.')
        await self.eval_guild(message.channel.guild.id, force_reset)
        await message.channel.send('Guild has been re-evaluated.')

    # @commands.has_permissions(administrator=True, manage_messages=True, manage_roles=True)
    async def setoption_guild(self, message: discord.message.Message) -> None:
        "Set a configuration option. Send message in message.channel on failure."
        configuration = self.get_guild_configuration(message.guild.id)
        valid = []

        auid = message.author.id
        # If message author is either bot owner or guild owner,
        if auid in {OWNER_ID, message.guild.owner}:
            # give them access to everything
            valid += ['setoptionusers', 'address', 'channel', 'forcerefreshusers']
        # If not, if set option users is defined in configuration,
        elif 'setoptionusers' in configuration:
            # If message author is allowed to set options,
            if auid in configuration['setoptionusers']:
                # give them access to almost everything.
                valid += ['address', 'channel', 'forcerefreshusers']

        if not valid:
            await message.channel.send(
                'You do not have permission to set any options. If you feel this is a mistake, '\
                'please contact server admin(s) and have them give you permission.')
            return
        args = parse_args(message.content, 2)
        validops = get_valid_options(valid)

        if not args:
            await message.channel.send('No arguments.'+validops)
            return

        option = args[0].lower()
        if not option in valid:
            await message.channel.send('Invalid option.'+validops)
            return

        if len(args) < 2:
            msg = f'Insufficiant arguments for `{option}`.'
            base = '`clear`, a discord id, or the username of a new user to add to the '
            arghelp = {'address': 'Server address of a java edition minecraft server.',
                       'channel': 'Name of the discord channel to send join-leave messages to.',
                       'setoptionusers': base+'set option permission list.',
                       'forcerefreshusers': base+'force reset permission list.'}
            msg += '\nArgument required: '+arghelp[option]
            await message.channel.send(msg)
            return

        set_value = except_chars(args[1], AZUP+AZLOW+NUMS+'.:-#')
        if not set_value:
            await message.channel.send('Value to set must not be blank!')
            return

        value: Any = set_value
        if option == 'channel':
            channelnames = [chan.name for chan in message.guild.text_channels]
            if not args[1] in channelnames:
                await message.channel.send('Channel not found in this guild.')
                return
            value = args[1]
        elif option in {'setoptionusers', 'forcerefreshusers'}:
            if set_value.lower() == 'clear':
                value = []
            else:
                try:
                    id_value = int(set_value)
                except ValueError:
                    # DANGER
                    if not '#' in args[1]:
                        await message.channel.send(
                            'Username does not have discriminator (ex. #1234).')
                        return
                    member = message.guild.get_member_named(args[1])
                    if member is None:
                        await message.channel.send('User not found / User not in this guild.')
                        return
                    id_value = member.id
##                    member = message.guild.get_member(value)
##                    member = self.get_user(value)
                name = await self.get_user_name(id_value, message.guild.get_member)
                if name is None:
                    await message.channel.send('User not found / User not in this guild.')
                    return
                value = [id_value]
                if option in configuration:
                    if value[0] in configuration[option]:
                        await message.channel.send(f'User `{name}` already in this list!')
                        return
                    value = configuration[option]+value
                await message.channel.send(f'Adding user `{name}` (id `{value[-1]}`)')
        configuration[option] = value
        self.write_guild_configuration(message.channel.guild.id, configuration)
        await message.channel.send(f'Updated value of option `{option}` to `{value}`.')
        force_reset = option in ('address', 'channel')
        await self.refresh(message, force_reset)

    async def setoption_dm(self, message: discord.message.Message) -> None:
        "Set a configuration option. Send message in message.channel on failure."
        configuration = self.get_dm_configuration()
        valid = []
        if message.author.id == OWNER_ID:
            valid += ['setoptionusers', 'updateusers', 'stopusers']
        elif 'setoptionusers' in configuration:
            if message.author.id in configuration['setoptionusers']:
                valid += ['updateusers', 'stopusers']

        if not valid:
            await message.channel.send('You do not have permission to set any options.')
            return
        args = parse_args(message.clean_content, 1)
        validops = get_valid_options(valid)

        if not args:
            await message.channel.send('Invalid option.'+validops)
            return

        option = args[0].lower()

        if option not in valid:
            await message.channel.send('Invalid option.'+validops)
            return

        if len(args) < 2:
            msg = f'Insufficiant arguments for {option}.'
            base = '`clear`, a discord user id, or the username of a new user to add'\
                   ' to the permission list of users who can '
            arghelp = {'stopusers': base+'stop the bot.',
                       'updateusers': base+'update the bot.',
                       'setoptionusers': base+'change stop and update permissions.'}
            msg += '\nArgument required: '+arghelp[option]
            await message.channel.send(msg)
            return
        value = args[1]
        if not value:
            await message.channel.send('Value to set must not be blank!')
            return
        if value.lower() == 'clear':
            value = []
        else:
            try:
                value = int(value)
            except ValueError:
                # DANGER
                if not '#' in args[1]:
                    await message.channel.send(
                        'Username does not have discriminator (ex. #1234).')
                    return
                member = await self.search_for_member_in_guilds(value)
                if member is None:
                    await message.channel.send('User not found.')
                    return
                value = member.id
##                name = self.get_user(value)
            name = await self.get_user_name(value)
            if name is None:
                await message.channel.send('User not found.')
                return
            value = [value]
            if option in configuration:
                if value[0] in configuration[option]:
                    await message.channel.send(
                        f'User `{name}` (id `{value[-1]}`) already in this list!')
                    return
                value = configuration[option]+value
            await message.channel.send(f'Adding user `{name}` (id `{value[-1]}`)')
        configuration[option] = value
        self.write_dm_configuration(configuration)
        await message.channel.send(f'Updated value of option `{option}` to `{value}`.')

    async def process_command_message(self, message: discord.message.Message, mode: str='guild') -> None:
        "Process new command message. Calls self.command[command](message)."
        err = ' Please enter a valid command. Use `{}help` to see valid commands.'
        # 1 if it's guild, 0 if direct message.
        midx = int(mode.lower() == 'guild')
        # Format error text depending on if direct or guild message.
        err = err.format(('', self.prefix+' ')[midx])
        # Command list depends on direct or guild too.
        commands = (self.dcommands, self.gcommands)[midx]
        # Get content of message.
        content = message.content

        # If no space in message
        if not ' ' in content:
            # If it's a guild message
            if midx:
                if content == self.prefix:
                    await message.channel.send('No command given.'+err)
                return
            # Prefix doesn't have to be there in direct, so add space so arguments work right.
            content += ' '
        args = parse_args(content)

        # Get command. zeroth if direct, first if guild because of prefix.
        command = args[midx].lower()

        if self.stopped.is_set() and midx:
            await message.channel.send(f'{__title__} is in the process of shutting down.')
            return

        # If command is valid, run it.
        if command in commands:
            await commands[command](message)
            return
        if not midx and content.startswith(self.prefix):
            # if in a direct message and starts with our prefix,
            await message.channel.send(
                "When you talk to me in DMs, there is no need to start with"\
                "my prefix for me to react!"
            )
            return
        # Otherwise, send error of no command.
        await message.channel.send('No valid command given.'+err)

    # Intents.guilds
    async def on_guild_join(self, guild: discord.guild.Guild) -> None:
        "Evaluate guild."
        msg = f'Guild gained: {guild.name} (id: {guild.id})'
        print(msg)
        append_file(self.logpath, '#'*8+msg+'#'*8)
        await self.eval_guild(guild.id, True)

    # Intents.guilds
    async def on_guild_remove(self, guild: discord.guild.Guild) -> None:
        "Remove configuration file for guild we are no longer in."
        msg = f'Guild lost: {guild.name} (id: {guild.id})\nDeleting guild settings'
        print(msg)
        append_file(self.logpath, '#'*8+msg+'#'*8)
        os.remove(self.get_guild_configuration_file(guild.id))

    # Intents.dm_messages, Intents.guild_messages, Intents.messages
    async def on_message(self, message: discord.message.Message) -> None:
        "React to any new messages."
        # Skip messages from ourselves.
        if message.author == self.user:
            return

        # If we can send message to person,
        if hasattr(message.channel, 'send'):
            # If message is from a guild,
            if isinstance(message.guild, discord.guild.Guild):
                # If message starts with our prefix,
                args = parse_args(message.clean_content.lower())
                pfx = args[0] == self.prefix if len(args) >= 1 else False
##                pfx = message.clean_content.lower().startswith(self.prefix)
                # of it starts with us being mentioned,
                ment = False
                if message.content.startswith('<@'):
                    new = message.content.replace('!', '')
                    new = new.replace('&', '')
                    ment = new.startswith(self.user.mention)
                if pfx or ment:
                    # we are, in reality, the fastest typer in world. aw yep.
                    async with message.channel.typing():
                        # Process message as guild
                        await self.process_command_message(message, 'guild')
                return
            # Otherwise, it's a direct message, so process it as one.
            async with message.channel.typing():
                await self.process_command_message(message, 'dm')
        # can't send messages so skip.

    # Default, not affected by intents
    async def on_error(self, event: str, *args, **kwargs) -> None:# pylint: disable=arguments-differ
        "Log error and continue."
        if event == 'on_message':
            print(f'Unhandled message: {args[0]}')
        extra = 'Error Event:\n'+str(event)+'\n'
        extra += 'Error args:\n'+'\n'.join(map(str, args))+'\nError kwargs:\n'
        extra += '\n'.join(f'{key}:{val}' for key, val in kwargs.items())
        log_active_exception(self.logpath, extra=extra)

    # Default, not affected by intents
    async def close(self) -> None:
        "Tell guilds bot shutting down."
        self.stopped.set()
        print('\nShutting down gears.')
        await gears.BaseBot.close(self)
        print('\nGears shut down...\nTelling guilds bot is shutting down.\n')
        async def tell_guild_shutdown(guild: discord.guild.Guild) -> None:
            channel = self.guess_guild_channel(guild.id)
            await channel.send(f'{__title__} is shutting down.')
        coros = (tell_guild_shutdown(guild) for guild in self.guilds)
        await asyncio.gather(*coros)

        print('Waiting to aquire updating lock...\n')
        with self.updating:
            print('Closing...')
            await discord.Client.close(self)

def run() -> None:
    "Run bot."
    if TOKEN is None:
        print('''\nNo token set!
Either add ".env" file in bots folder with DISCORD_TOKEN=<token here> line,
or set DISCORD_TOKEN environment variable.''')
        return
    print('\nStarting bot...')

    intents = discord.Intents(
        dm_messages = True,
        guild_messages = True,
        messages = True,
        guilds = True,
        members = True)
    # 4867

    loop = asyncio.new_event_loop()

    bot = StatusBot(BOT_PREFIX, loop=loop, intents=intents)

    try:
        loop.run_until_complete(bot.start(TOKEN))
    except KeyboardInterrupt:
        print('\nClosing bot...')
        loop.run_until_complete(bot.close())
    finally:
        # cancel all lingering tasks
        loop.close()
        print('\nBot has been deactivated.')
    return

if __name__ == '__main__':
    print(f'{__title__} v{__version__}\nProgrammed by {__author__}.')
##    logging.basicconfig(level=logging.INFO)
    run()
##    logging.shutdown()
