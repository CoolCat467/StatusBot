#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# StatusBot for Discord

"Status Bot for Discord using Python 3"

# Programmed by CoolCat467

__title__ = 'StatusBot'
__author__ = 'CoolCat467'
__version__ = '0.3.1'
__ver_major__ = 0
__ver_minor__ = 3
__ver_patch__ = 1

# https://discordpy.readthedocs.io/en/latest/index.html
# https://discord.com/developers

import os
import asyncio
import json
import math
import random
import traceback
import concurrent.futures
from typing import Union
from threading import Event, Lock
import logging
import binascii
import base64

from dotenv import load_dotenv
import discord
##from discord.ext import tasks, commands

# Update talks to raw.githubusercontent.com.
import update

# server_status is basically mcstatus from
# https://github.com/Dinnerbone/mcstatus
# with some slight modifications to make it better,
# expecially asyncronous stuff.
from status import server_status as mc

# Gears is basically like discord's Cogs, but
# by me.
import gears

# Aquire token.
# Looks for file named ".env",
# file line 1 is "# .env",
# file line 2 is "DISCORD_TOKEN=XXXXX"
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

BOT_PREFIX = '!status'
OWNER_ID = 344282497103691777

# Text globals
AZUP = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
AZLOW = AZUP.lower()
NUMS = '0123456789'


def write_file(filename:str, data:str) -> None:
    "Write data to file <filename>."
    filename = os.path.abspath(filename)
    with open(filename, 'w', encoding='utf-8') as wfile:
        wfile.write(data)
        wfile.close()

def append_file(filename:str, data:str) -> None:
    "Add data to file <filename>."
    filename = os.path.abspath(filename)
    if os.path.exists(filename):
        with open(filename, 'a', encoding='utf-8') as wfile:
            wfile.write(data)
            wfile.close()
    else:
        write_file(filename, data)

def read_file(filename:str) -> Union[str, None]:
    "Read data from file <filename>. Return None if file does not exist."
    filename = os.path.abspath(filename)
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as rfile:
            data = rfile.read()
            rfile.close()
        return data
    return None

def read_json(filename:str) -> Union[dict, None]:
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

def write_json(filename:str, dictionary:dict, indent:int=2) -> None:
    "Write dicitonary as json to filename."
    filename = os.path.abspath(filename)
    with open(filename, 'w', encoding='utf-8') as wfile:
        try:
            json.dump(dictionary, wfile, indent=indent)
        finally:
            wfile.close()

def split_time(seconds:int) -> list:
    "Split time into decades, years, months, weeks, days, hours, minutes, and seconds."
    seconds = int(seconds)
    def mod_time(sec:int, num:int) -> tuple:
        "Return number of times sec divides equally by number, then remainder."
        smod = sec % num
        return int((sec - smod) // num), smod
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

def combine_and(data:list) -> str:
    "Join values of text, and have 'and' with the last one properly."
    data = list(data)
    if len(data) >= 2:
        data[-1] = 'and ' + data[-1]
    if len(data) > 2:
        return ', '.join(data)
    return ' '.join(data)

def format_time(seconds:int, single_title_allowed:bool=False) -> str:
    "Returns time using the output of split_time."
    times = ('eons', 'eras', 'epochs', 'ages', 'millenniums',
             'centuries', 'decades', 'years', 'months', 'weeks',
             'days', 'hours', 'minutes', 'seconds')
    single = [i[:-1] for i in times]
    single[5] = 'century'
    split = split_time(seconds)
    zip_idx_values = [(i, v) for i, v in enumerate(split) if v]
    if single_title_allowed:
        if len(zip_idx_values) == 1:
            index, value = zip_idx_values[0]
            if value == 1:
                return 'a '+single[index]
    data = []
    for index, value in zip_idx_values:
        title = single[index] if abs(value) < 2 else times[index]
        data.append(str(value)+' '+title)
    return combine_and(data)

def get_time_of_day(hour:int) -> str:
    "Figure out and return what time of day it is."
    if hour > 4 and hour < 12:
        return 'Morning'
    if hour > 11 and hour < 19:
        # "It is usually from 12 PM to 6 PM,
        # but during winter it may be from 12 PM to 4 PM
        # and during summer it may be from 12 PM to 8 PM."
        return 'Afternoon'
    if hour > 18 and hour < 22:
        return 'Evening'
    ##if hour > 21 or hour < 4:
    return 'Night'

def except_chars(text:str, valid:str=AZUP+AZLOW+NUMS+'.:-') -> str:
    "Return every character in text that is also in valid string."
    return ''.join(i for i in text if i in valid)

def parse_args(string:str, ignore:int=0, sep:str=' ') -> list:
    "Return a list of arguments by splitting string by sep, ommiting first ignore args."
    return string.split(sep)[ignore:]

def wrap_list_values(items:tuple, wrap:str='`') -> list:
    "Wrap all items in list of strings with wrap. Ex. ['cat'] -> ['`cat`']"
    return [wrap+str(i)+wrap for i in iter(items)]

def log_active_exception(logpath, extra=None) -> None:
    "Log active exception."
    # Get values from exc_info
    values = os.sys.exc_info()
    # Get error message.
    msg = '#'*16+'\n'
    if not extra is None:
        msg += str(extra)+'\n'
    msg += 'Exception class:\n'+str(values[0])+'\n'
    msg += 'Exception text:\n'+str(values[1])+'\n'
    class FakeFile:
        "Fake file class implementing write attribute."
        def __init__(self):
            self.data = []
        def write(self, value:str) -> None:
            "Append value to data."
            self.data.append(value)
        def getdata(self) -> str:
            "Return data collected."
            return ''.join(self.data)[:-1]
    yes_totaly_a_file = FakeFile()
    traceback.print_exception(None, values[1],
                              values[2],
                              file=yes_totaly_a_file)
    msg += 'Traceback:\n'+yes_totaly_a_file.getdata()+'\n'
    msg += '#'*16+'\n'
##    print(msg)
    logging.exception(msg)
    append_file(logpath, msg)

async def send_over_2000(send_func, text:str, wrap_with:str='',
                         replace_existing_wrap:bool=True) -> None:
    "Use send_func to send text in segments over 2000 characters by"\
    "splitting it into multiple messages."
    send = str(text)
    add_aloc = 0
    if wrap_with:
        if replace_existing_wrap:
            send = send.replace(wrap_with, '')
        add_aloc = int(len(wrap_with) * 2)
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
    if wrap_with:
        parts = wrap_list_values(parts, wrap_with)
    # This would be great for asyncio.gather, but
    # I'm not sure if that will throw off call order or not.
##    coros = [send_func(part) for part in parts]
##    await asyncio.gather(*coros)
    for part in parts:
        await send_func(part)
    return None

async def get_github_file(path:str, timeout:int=10) -> str:
    "Return text from github file in this project decoded as utf-8"
    file = await update.get_file(__title__, path, __author__, 'master', timeout)
    return file.decode('utf-8')

class PingState(gears.AsyncState):
    "State where we ping server."
    __slots__ = 'failed', 'exit_ex'
    def __init__(self):
        super().__init__('ping')
        self.failed = False
        self.exit_ex = None
    
    async def entry_actions(self) -> None:
        "Reset failed to false and exception to None."
        self.failed = False
        self.exit_ex = None
        self.machine.last_delay = math.inf
        self.machine.last_ping = set()
        return None
    
    async def do_actions(self) -> None:
        "Ping server. If failure, self.falied = True and if exceptions, save."
        try:
            json_data, ping = await self.machine.server.async_status()
        except Exception as ex:
            self.exit_ex = f'`A {type(ex).__name__} Exception Has Occored'
            if ex.args:
                sargs = list(map(str, ex.args))
                self.exit_ex += ': '+wrap_list_values(combine_and(sargs), '"')
            self.exit_ex += '`'
            self.failed = True
##            print(self.exit_ex)
            # No need to record detailed errors for timeouts.
            ignore = (concurrent.futures.TimeoutError,
                      asyncio.exceptions.TimeoutError,
                      ConnectionRefusedError)
            if not isinstance(ex, ignore):
                log_active_exception(self.machine.bot.logpath)
            return None
        # If success, get players.
        self.machine.last_json = json_data
        self.machine.last_delay = ping
        current = []
        if 'players' in json_data and 'sample' in json_data['players']:
            for player in json_data['players']['sample']:
                if 'name' in player:
                    current.append(player['name'])
        current = set(current)
        # If different players,
        if current != self.machine.last_ping:
            # Find difference in players.
            joined = tuple(current.difference(self.machine.last_ping))
            left = tuple(self.machine.last_ping.difference(current))
            
            # Update last ping.
            self.machine.last_ping = current
            
            def users_mesg(action:str, users:list) -> str:
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
##        elif 'players' in json_data and 'online' in json_data['players']:
##            print(json_data['players']['online'])
        return None
    
    async def check_conditions(self) -> Union[str, None]:
        "If there was failure to connect to server, await restart."
        if self.failed:
            return 'await_restart'
        return None
    
    async def exit_actions(self) -> None:
        "When exiting, if we collected an exception, send it to channel."
        if not self.exit_ex is None:
            await self.machine.channel.send(self.exit_ex)
        return None

class WaitRestartState(gears.AsyncState):
    "State where we wait for server to restart."
    __slots__ = 'ignore_ticks', 'success', 'ticks', 'ping'
    def __init__(self, ignore_ticks:int):
        super().__init__('await_restart')
        self.ignore_ticks = ignore_ticks
        self.success = None
        self.ticks = 0
        self.ping = None
    
    async def entry_actions(self) -> None:
        "Reset failed and say connection lost."
        extra = ''
        if not self.machine.last_delay in {math.inf, 0}:
            extra = f' Last successful ping latency was `{self.machine.last_delay}ms`'
        await self.machine.channel.send('Connection to server has been lost.'+extra)
        self.success = False
        self.ticks = 0
        self.ping = 0
        return None
    
    async def attempt_contact(self) -> bool:
        "Attempt to talk to server."
        try:
            self.ping = await self.machine.server.async_ping()
        except Exception:
            pass
        else:
            return True
        return False
    
    async def do_actions(self) -> None:
        "Every once and a while try to talk to server again."
        self.ticks = (self.ticks + 1) % self.ignore_ticks
        
        if self.ticks == 0:
            self.success = await self.attempt_contact()
    
    async def check_conditions(self) -> None:
        "If contact attempt was sucessfull, switch back to ping."
        if self.success:
            return 'ping'
        return None
    
    async def exit_actions(self) -> None:
        "Tell guild connection re-established."
        await self.machine.channel.send(
            f'Connection to server re-established with a ping of `{self.ping}ms`.')
        return None

class GuildServerPinger(gears.StateTimer):
    "Server pinger for guild."
    __slots__ = 'guildid', 'server', 'last_ping', 'last_json', 'last_delay', 'channel'
    tickspeed = 60
    waitticks = 5
    def __init__(self, bot:discord.Client, guildid:int) -> None:
        "Needs bot we work for, and id of guild we are pinging the server for."
        self.guildid = guildid
        super().__init__(bot, self.guildid, self.tickspeed)
        self.server = mc.Server('')
        self.last_ping = set()
        self.last_json = {}
        self.last_delay = 0
        self.channel = None
        
        self.add_state(PingState())
        self.add_state(WaitRestartState(self.waitticks))
    
    @property
    def wait_time(self):
        "Total wait time when in await_restart state."
        return self.tickspeed * self.waitticks
    
    async def initialize_state(self) -> None:
        "Set state to ping."
        await self.set_state('ping')
        return None
    
    async def start(self) -> None:
        "If config is good, run pinger."
        config = self.bot.get_guild_config(self.guildid)
        self.channel = self.bot.guess_guild_channel(self.guildid)
        if 'address' in config:
            self.server = mc.Server.lookup(config['address'])
            try:
                await super().start()
            except Exception:
                log_active_exception(self.bot.logpath)
            finally:
                await self.channel.send('Server pinger stopped.')
        else:
            await self.channel.send('No address for this guild defined, pinger not started.')
        return None

def get_valid_options(valid:list, wrap:str='`') -> str:
    "Return string of ' Valid options are: {valid}' but with pretty formatting."
    validops = combine_and(wrap_list_values(valid, wrap))
    return f' Valid options are: {validops}.'

async def send_command_list(commands:dict, name:str, channel) -> str:
    "Send message on channel telling user about all valid name commands."
    sort = sorted(commands.keys(), reverse=True)
    commands = '\n'.join(wrap_list_values(sort, '`'))
    text = f"{__title__}'s Valid {name} Commands:"
    await channel.send(text)
    await send_over_2000(channel.send, commands)

class StatusBot(discord.Client, gears.BaseBot):
    "StatusBot needs prefix, eventloop, and any arguments to pass to discord.Client."
    def __init__(self, prefix:str, *args, loop=asyncio.get_event_loop(), **kwargs):
        self.loop = loop
        discord.Client.__init__(self, *args, loop=self.loop, **kwargs)
        self.stopped = Event()
        self.updating = Lock()
        self.prefix = prefix
        self.rootdir = os.path.split(os.path.abspath(__file__))[0]
        self.logpath = os.path.join(self.rootdir, 'log.txt')
        self.gcommands = {'currentversion': self.getcurrentvers,
                          'onlineversion': self.getonlinevers,
                          'getmyid': self.getmyid,
                          'getjson': self.getjson,
                          'getfavicon': self.getfavicon,
                          'getonline': self.getonline,
                          'getping': self.getping,
                          'refresh': self.refresh,
                          'setoption': self.setoption_guild,
                          'getoption': self.getoption_guild,
                          'help': self.help_guild}
        self.dcommands = {'currentversion': self.getcurrentvers,
                          'onlineversion': self.getonlinevers,
                          'getmyid': self.getmyid,
                          'stop': self.stop,
                          'update': self.update,
                          'setoption': self.setoption_dm,
                          'getoption': self.getoption_dm,
                          'help': self.help_dm}
        gears.BaseBot.__init__(self, self.loop)
    
    def __repr__(self):
##        up = self.__class__.__weakref__.__qualname__.split('.')[0]
        return f'<{self.__class__.__name__} Object>'# ({up} subclass)>'
    
    @property
    def gear_close(self):
        "Return True if gears should close."
        return self.stopped.is_set() or self.is_closed()
    
    def get_guild_config_file(self, guildid:int) -> str:
        "Return the path to the config json file for a ceartain guild id."
        return os.path.join(self.rootdir, 'config', 'guilds', str(guildid)+'.json')
    
    def get_dm_config_file(self) -> str:
        "Return the path to the config json file for all DMs."
        return os.path.join(self.rootdir, 'config', 'dms.json')
    
    def get_guild_config(self, guildid:int) -> dict:
        "Return a dictionary from the json read from guild config file."
        guildfile = self.get_guild_config_file(guildid)
        guildconfig = read_json(guildfile)
        if guildconfig is None:
            # Guild does not have config
            # Therefore, create file for them
            write_file(guildfile, '{}')
            guildconfig = {}
        return guildconfig
    
    def get_dm_config(self) -> dict:
        "Return a dictionary from the json read from the DMs config file."
        dmfile = self.get_dm_config_file()
        dmconfig = read_json(dmfile)
        if dmconfig is None:
            write_file(dmfile, '{}')
            dmconfig = {}
        return dmconfig
    
    def write_guild_config(self, guildid:int, config:dict) -> None:
        "Write guild config file from config dictionary."
        guildfile = self.get_guild_config_file(guildid)
        write_file(guildfile, json.dumps(config, indent=2))
    
    def write_dm_config(self, config:dict) -> None:
        "Write DMs config file from config dictionary."
        dmfile = self.get_dm_config_file()
        write_file(dmfile, json.dumps(config, indent=2))
    
    def guess_guild_channel(self, gid:int):
        "Guess guild channel and return channel."
        guild = self.get_guild(gid)
        config = self.get_guild_config(gid)
        valid = [chan.name for chan in guild.text_channels]
        if 'channel' in config:
            channelname = config['channel']
            if channelname in valid:
                channel = discord.utils.get(guild.text_channels, name=channelname)
                return channel
        expect = [cname for cname in valid if 'bot' in cname.lower()]
        expect += ['general']
        for channel in guild.text_channels:
            if channel.name in expect:
                return channel
        return random.choice(guild.text_channels)
    
    async def search_for_member_in_guilds(self, username):
        "Search for member in all guilds we connected to. Return None on failure."
        members = (guild.get_member_named(username) for guild in self.guilds)
        for member in members:
            if not member is None:
                return member
        return
    
    async def add_guild_pinger(self, gid:int, force_reset:bool=False) -> str:
        "Create server pinger for guild if not exists. Return 'started', 'restarted', or 'none'."
        if not gid in self.gears:
            self.add_gear(GuildServerPinger(self, gid))
            return 'started'
        if force_reset or not self.gears[gid].running:
            if not self.gears[gid].stopped:
                await self.gears[gid].hault()
            self.remove_gear(gid)
            self.add_gear(GuildServerPinger(self, gid))
            return 'restarted'
        return 'none'
    
    async def eval_guild(self, guildid:int, force_reset:bool=False) -> int:
        "(Re)Start guild pinger if able. Otherwise tell them to change settings."
        guildconfig = self.get_guild_config(guildid)
        channel = self.guess_guild_channel(guildid)
        if not 'channel' in guildconfig:
            await channel.send('This is where I will post leave-join messages'\
                               'until an admin sets my `channel` option.')
        if 'address' in guildconfig:
            action = await self.add_guild_pinger(guildid, force_reset)
            if action != 'none':
                await channel.send(f'Server pinger {action}.')
            else:
                await channel.send('No action taken.')
        else:
            await channel.send('Server address not set, pinger not started.'\
                               f'Please set it with `{self.prefix} setoption address <address>`.')
        return guildid
    
    async def eval_guilds(self, force_reset:bool=False) -> list:
        "Evaluate all guilds. Return list of guild ids evaluated."
        coros = (self.eval_guild(guild.id, force_reset) for guild in self.guilds)
        return await asyncio.gather(*coros)
    
    # Default, not affected by intents.
    async def on_ready(self) -> None:
        "Print information about bot and evaluate all guilds."
        logging.info(f'{self.user} has connected to Discord!')
        logging.info(f'Prefix: {self.prefix}')
        logging.info(f'Intents: {self.intents}')
        logging.info(f'Root Dir: {self.rootdir}')
        
        configdir = os.path.join(self.rootdir, 'config')
        if not os.path.exists(configdir):
            os.mkdir(configdir)
        guilddir = os.path.join(configdir, 'guilds')
        if not os.path.exists(guilddir):
            os.mkdir(guilddir)
        favicondir = os.path.join(self.rootdir, 'favicon')
        if not os.path.exists(favicondir):
            os.mkdir(favicondir)
        
        logging.info(f'\n{self.user} is connected to the following guilds:\n')
        guildnames = []
        for guild in self.guilds:
            guildnames.append(f'{guild.name} (id: {guild.id})')
        spaces = max(len(name) for name in guildnames)
        logging.info('\n'+'\n'.join(name.rjust(spaces) for name in guildnames)+'\n')
        ids = await self.eval_guilds(True)
        logging.info('Guilds evaluated:\n'+'\n'.join([str(x) for x in ids])+'\n')
        act = discord.Activity(type=discord.ActivityType.watching, name=f'for {self.prefix}')
        await self.change_presence(status=discord.Status.online, activity=act)
        return
    
    async def get_user_name(self, uid:int, getmember=None) -> Union[str, None]:
        "Return the name of user with id <uid>."
        if getmember is None:
            getmember = self.get_user
        member = getmember(uid)
        if member is None:
            return member
        return member.name+'#'+member.discriminator
    
    async def replace_ids_w_names(self, names:tuple) -> list:
        "Replace user ids (intigers) with usernames in lists. Returns list of strings."
        replaced = []
        for item in names:
            if isinstance(item, int):
                username = await self.get_user_name(item)
                if not username is None:
                    replaced.append(f'{username} (id. {item})')
                    continue
            replaced.append(str(item))
        return replaced
    
    async def getmyid(self, message) -> None:
        "Tell the author of the message their user id."
        await message.channel.send(f'Your user id is `{message.author.id}`.')
        return
    
    async def save_favicon(self, guildid:int) -> None:
        "Save favicon image to favicon folder for this guild's server"
        if guildid in self.gears:
            pinger = self.gears[guildid]
            if pinger.active_state.name != 'ping':
                return
            if not 'favicon' in pinger.last_json:
                return
            favicon_data = pinger.last_json['favicon']
            if not favicon_data.startswith('data:image/png;base64,'):
                return
            favicon_data = favicon_data.split(',')[1]
            try:
                data = base64.b64decode(favicon_data)
                filename = os.path.join(self.rootdir, 'favicon', f'{guildid}.png')
                filename = os.path.abspath(filename)
                with open(filename, mode='wb') as favicon_file:
                    favicon_file.write(data)
                    favicon_file.close()
            except binascii.Error as ex:
                logging.info('Encountered error decoding base64 string for favicon.')
    
    async def getfavicon(self, message) -> None:
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
    
    async def getjson(self, message) -> None:
        "Tell the author of the message the last json from server pinger."
        if message.guild.id in self.gears:
            pinger = self.gears[message.guild.id]
            if pinger.active_state is None:
                await message.channel.send('Server pinger is not active for this guild. '+
                                           'Use command `refresh` to restart.')
                return
            if pinger.active_state.name == 'ping':
                lastdict = pinger.last_json
                if 'favicon' in lastdict:
                    favicon = lastdict['favicon']
                    lastdict['favicon'] = '<base64 image data>'
                msg = json.dumps(lastdict, sort_keys=True, indent=2)
                await message.channel.send('Last received json message:')
                await send_over_2000(message.channel.send, msg, '```', False)
                return
            delay = format_time(pinger.wait_time)
            await message.channel.send(
                f'Cannot connect to server at this time, try again in {delay}.')
            return
        await message.channel.send('Server pinger is not running for this guild.')
        return
    
    async def getping(self, message) -> None:
        "Tell the author of the message the bot's latency to the guild's server."
        if message.guild.id in self.gears:
            pinger = self.gears[message.guild.id]
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
        await message.channel.send('Server pinger is not running for this guild.')
        return
    
    async def getonline(self, message) -> None:
        "Tell author of the message the usernames of the players connected to the guild's server."
        if message.guild.id in self.gears:
            pinger = self.gears[message.guild.id]
            if pinger.active_state is None:
                await message.channel.send('Server pinger is not active for this guild. '+
                                           'Use command `refresh` to restart.')
                return
            if pinger.active_state.name == 'ping':
                players = list(pinger.last_ping)
                if players:
                    players = combine_and(wrap_list_values(players, '`'))
                    await message.channel.send('Players online in last received sample:')
                    await send_over_2000(message.channel.send, players)
                    return
                await message.channel.send('No players were online in the last received sample.')
                return
            delay = format_time(pinger.wait_time)
            await message.channel.send(
                f'Cannot connect to server at this time, try again in {delay}.')
            return
        await message.channel.send('Server pinger is not running for this guild.')
        return
    
    async def stop(self, message) -> None:
        "Stop this bot. Sends stop message."
        config = self.get_dm_config()
        if not 'stopusers' in config:
            await message.channel.send('No one has permission to run this command.')
            return
        
        if message.author.id in config['stopusers']:
            await message.channel.send('Stopping...')
            # Set stopped event
            self.stopped.set()
            def close_bot():
                self.loop.create_task(self.close())
            self.loop.call_later(3, close_bot)
            return
        await message.channel.send('You do not have permission to run this command.')
        return
    
    async def getcurrentvers(self, message) -> tuple:
        "Get current version, tell user in message.channel, and return that version as tuple."
        proj_root = os.path.split(self.rootdir)[0]
        version = read_file(os.path.join(proj_root, 'version.txt'))
        await message.channel.send(f'Current version: {version}')
##        return (__ver_major__, __ver_minor__, __ver_patch__)
        return tuple(map(int, version.strip().split('.')))
    
    async def getonlinevers(self, message) -> tuple:
        "Get online version, tell user in message.channel, and return said version as tuple."
        # Get github version string
        version = await get_github_file('version.txt')
        # Send message about it.
        await message.channel.send(f'Online version: {version}')
        # Make it tuple and return it
        return tuple(map(int, version.strip().split('.')))
    
    async def update(self, message, timeout:int=20) -> None:
        "Preform update from github."
        if self.stopped.is_set():
            await message.channel.send(
                f'{__title__} is in the process of shutting down, canceling update.')
            return
        config = self.get_dm_config()
        if not 'updateusers' in config:
            await message.channel.send('No one has permission to run this command.')
            return
        if message.author.id in config['updateusers']:
            self.updating.acquire()
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
                except Exception:
                    # On failure, tell them we can't read file.
                    await message.channel.send('Could not read file list. Aborting update.')
                    self.updating.release()
                    return
                # Get max amount of time this could take.
                maxtime = format_time(timeout*len(paths))
                # Stop everything if we are trying to shut down.
                if self.stopped.is_set():
                    await message.channel.send(
                        f'{__title__} is in the process of shutting down, canceling update.')
                    self.updating.release()
                    return
                # Tell user number of files we are updating.
                await message.channel.send(f'{len(paths)} files will now be updated. '\
                                           f'Please wait. This may take up to {maxtime} at most.')
                # Update said files.
                rootdir = os.path.split(self.rootdir)[0]
                await update.update_files(rootdir, paths, __title__, __author__, 'master', timeout)
                await message.channel.send('Done. Bot will need to be restarted to apply changes.')
                self.updating.release()
                return
            await message.channel.send('No update required.')
            self.updating.release()
            return
        await message.channel.send('You do not have permission to run this command.')
        return
    
    async def getoption_guild(self, message) -> None:
        "Send message with value of option given in this guild's config."
        args = parse_args(message.content, 2)
        config = self.get_guild_config(message.guild.id)
        valid = tuple(config.keys())
        
        if not valid:
            await message.channel.send('No options are set at this time.')
            return
        validops = get_valid_options(valid)            
        
        if not args:
            await message.channel.send('Invalid option.'+validops)
            return
        option = args[0].lower()
        if option in valid:
            value = config[option]
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
    
    async def getoption_dm(self, message) -> None:
        "Send message with value of option given in the dm config."
        args = parse_args(message.content, 1)
        config = self.get_dm_config()
        valid = []
        if message.author.id == OWNER_ID:
            valid += ['setoptionusers', 'updateusers', 'stopusers']
        elif 'setoptionusers' in config:
            if message.author.id in config['setoptionusers']:
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
                value = config[option]
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
        return
    
    async def help_guild(self, message) -> None:
        "Send a message on message.channel telling user about all valid options."
        await send_command_list(self.gcommands, 'Guild', message.channel)
        return
    
    async def help_dm(self, message) -> None:
        "Send a message on message.channel telling user about all valid options."
        await send_command_list(self.dcommands, 'DM', message.channel)
        return
    
    async def refresh(self, message, force_reset:bool=False) -> None:
        "Re-evaluate guild, then tell them it happened."
        if force_reset:
            await message.channel.send('Replacing server pinger might take a bit, '\
                                       'we have to let the old one realize it should stop.')
        await self.eval_guild(message.channel.guild.id, force_reset)
        await message.channel.send('Guild has been re-evaluated.')
        return
    
    # @commands.has_permissions(administrator=True, manage_messages=True, manage_roles=True)
    async def setoption_guild(self, message) -> None:
        "Set a config option. Send message in message.channel on falure."
        config = self.get_guild_config(message.guild.id)
        valid = []
        
        auid = message.author.id
        # If message author is either bot owner or guild owner,
        if auid in {OWNER_ID, message.guild.owner}:
            # give them access to everything
            valid += ['setoptionusers', 'address', 'channel']
        # If not, if setoptionusers is defined in config,
        elif 'setoptionusers' in config:
            # If message author is allowed to set options,
            if auid in config['setoptionusers']:
                # give them access to almost everything.
                valid += ['address', 'channel']
        
        if not valid:
            await message.channel.send(
                'You do not have permission to set any options. If you feel this is a mistake,'\
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
            msg = f'Insufficiant arguments for {option}.'
            base = '`clear`, a discord id, or the username of a new user to add to the '
            arghelp = {'address': 'Server address of a java edition minecraft server.',
                       'channel': 'Name of the discord channel to send join-leave messages to.',
                       'setoptionusers': base+'permission list.'}
            msg += '\nArgument required: '+arghelp[option]
            await message.channel.send(msg)
            return
        
        value = except_chars(args[1], AZUP+AZLOW+NUMS+'.:-#')
        if option == 'channel':
            channelnames = [chan.name for chan in message.guild.text_channels]
            if not args[1] in channelnames:
                await message.channel.send('Channel not found in this guild.')
                return
            value = args[1]
        elif option == 'setoptionusers':
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
                    member = message.guild.get_member_named(args[1])
                    if member is None:
                        await message.channel.send('User not found / User not in this guild.')
                        return
                    value = member.id
##                    member = message.guild.get_member(value)
##                    member = self.get_user(value)
                name = await self.get_user_name(value, message.guild.get_member)
                if name is None:
                    await message.channel.send('User not found / User not in this guild.')
                    return
                value = [value]
                if option in config:
                    if value[0] in config[option]:
                        await message.channel.send(f'User `{name}` already in this list!')
                        return
                    value = config[option]+value
                await message.channel.send(f'Adding user `{name}` (id `{value[-1]}`)')
        config[option] = value
        self.write_guild_config(message.channel.guild.id, config)
        await message.channel.send(f'Updated value of option `{option}` to `{value}`.')
        force_reset = option in ('address', 'channel')
        await self.refresh(message, force_reset)
        return
    
    async def setoption_dm(self, message) -> None:
        "Set a config option. Send message in message.channel on falure."
        config = self.get_dm_config()
        valid = []
        if message.author.id == OWNER_ID:
            valid += ['setoptionusers', 'updateusers', 'stopusers']
        elif 'setoptionusers' in config:
            if message.author.id in config['setoptionusers']:
                valid += ['updateusers', 'stopusers']
        
        if not valid:
            await message.channel.send('You do not have permission to set any options.')
            return
        args = parse_args(message.clean_content, 1)
        validops = get_valid_options(valid)
        
        if not args:
            if valid:
                await message.channel.send('Invalid option.'+validops)
                return
            await message.channel.send('You do not have permission to set any options.')
            return
        
        option = args[0].lower()
        
        if option in valid:
            if len(args) < 2:
                msg = f'Insufficiant arguments for {option}.'
                base = '`clear`, a discord user id, or the username of a new user to add'\
                       'to the permission list of users who can '
                arghelp = {'stopusers': base+'stop the bot.',
                           'updateusers': base+'update the bot.',
                           'setoptionusers': base+'change stop and update permissions.'}
                msg += '\nArgument required: '+arghelp[option]
                await message.channel.send(msg)
                return
            value = args[1]
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
                if option in config:
                    if value[0] in config[option]:
                        await message.channel.send(
                            f'User `{name}` (id `{value[-1]}`) already in this list!')
                        return
                    value = config[option]+value
                await message.channel.send(f'Adding user `{name}` (id `{value[-1]}`)')
            config[option] = value
            self.write_dm_config(config)
            await message.channel.send(f'Updated value of option `{option}` to `{value}`.')
        return
    
    async def process_command_message(self, message, mode:str='guild') -> None:
        "Process new command message. Calls self.command[command](message)."
        err = ' Please enter a valid command. Use `{}help` to see valid commands.'
        # 1 if it's guild, 0 if dm.
        midx = int(mode.lower() == 'guild')
        # Format error text depending on if dm or guild message.
        err = err.format(('', self.prefix+' ')[midx])
        # Command list depends on dm or guild too.
        commands = (self.dcommands, self.gcommands)[midx]
        # Get content of message.
        content = message.content
        
        # If no space in message
        if not ' ' in content:
            # If it's a guild message
            if midx:
                # Prefix has to be there in guild message, so send error.
                await message.channel.send('No command given.'+err)
                return
            # Prefix doesn't have to be there in dm, so add space so args works right.
            content += ' '
        args = parse_args(content)
        # Get command. zeroth if dm, first if guild because of prefix.
        command = args[midx].lower()
        
        if self.stopped.is_set() and midx:
            await message.channel.send(f'{__title__} is in the process of shutting down.')
            return
        
        # If command is valid, run it.
        if command in commands:
            await commands[command](message)
            return
        if not midx and content.startswith(self.prefix):
            # if in a dm and starts with our prefix,
            await message.channel.send(
                "When you talk to me in DMs, there is no need to start with"\
                "my prefix for me to react!"
            )
            return
        # Otherwse, send error of no command.
        await message.channel.send('No valid command given.'+err)
        return
    
    # Intents.guilds
    async def on_guild_join(self, guild) -> None:
        "Evaluate guild."
        await self.eval_guild(guild.id, True)
        return
    
##    # Intents.members
##    async def on_member_join(self, member) -> None:
##        "Member joined a guild we are in."
##        pass
##    
##    # Intents.members
##    async def on_member_remove(self, member) -> None:
##        "Member left a guild we are in."
##        return None
    
    # Intents.guilds
    async def on_guild_remove(self, guild) -> None:
        "Remove config file for guild we are no longer in."
        msg = f'Guild lost: {guild.id}'
        logging.info(msg)
        append_file(self.logpath, '#'*8+msg+'#'*8)
        os.remove(self.get_guild_config_file(guild.id))
        return None
    
    # Intents.dm_messages, Intents.guild_messages, Intents.messages
    async def on_message(self, message) -> None:
        "React to any new messages."
        # Skip messages from ourselves.
        if message.author == self.user:
            return
        
        # If we can send message to person,
        if hasattr(message.channel, 'send'):
            # If message is from a guild,
            if isinstance(message.guild, discord.guild.Guild):
                # If message starts with our prefix,
                pfx = message.clean_content.lower().startswith(self.prefix)
                # of it starts with us being mentioned,
                ment = False
                if message.content.startswith('<@'):
                    new = message.content.replace('!', '')
                    new = new.replace('&', '')
                    ment = new.startswith(self.user.mention)
                if pfx or ment:
                    # we are, in reality, fastest typer in world. for sure.
                    async with message.channel.typing():
                        # Process message as guild
                        await self.process_command_message(message, 'guild')
                return
            # Otherwise, it's a dm, so process it as one.
            async with message.channel.typing():
                await self.process_command_message(message, 'dm')
        # can't send messages so skip.
        return
    
    # Default, not affected by intents
    async def on_error(self, event, *args, **kwargs) -> None:
        "Log error and continue."
        if event == 'on_message':
            logging.info(f'Unhandled message: {args[0]}')
        extra = 'Error Event:\n'+str(event)+'\n'
        extra += 'Error args:\n'+'\n'.join(map(str, args))+'\nError kwargs:\n'
        extra += '\n'.join(f'{key}:{val}' for key, val in kwargs.items())
        log_active_exception(self.logpath, extra=extra)
        return
    
    # Default, not affected by intents
    async def close(self) -> None:
        "Tell guilds bot shutting down."
        self.stopped.set()
        logging.info('\nShutting down gears.')
        await gears.BaseBot.close(self)
        logging.info('\nGears shut down...\nTelling guilds bot is shutting down.\n')
        async def tell_guild_shutdown(guild):
            channel = self.guess_guild_channel(guild.id)
            await channel.send(f'{__title__} is shutting down.')
            return
        coros = (tell_guild_shutdown(guild) for guild in self.guilds)
        await asyncio.gather(*coros)
        
        logging.info('Waiting to aquire updating lock...\n')
        self.updating.acquire()
        logging.info('Closing...')
        await discord.Client.close(self)
        self.updating.release()
        return

def run() -> None:
    "Run bot."
    if TOKEN is None:
        logging.critical('''\nNo token set!
Either add ".env" file in bots folder with DISCORD_TOKEN=<token here> line,
or set DISCORD_TOKEN environment variable.''')
        return
    logging.info('\nStarting bot...')
    
    loop = asyncio.get_event_loop()
##    intents = discord.Intents()
##    intents.dm_messages = True
##    intents.guild_messages = True
##    intents.messages = True
##    intents.guilds = True
##    intents.members = True
    intents = discord.Intents(
        dm_messages = True,
        guild_messages = True,
        messages = True,
        guilds = True,
        members = True)
    # 4867
    
    bot = StatusBot(BOT_PREFIX, loop=loop, intents=intents)
    
    try:
        loop.run_until_complete(bot.start(TOKEN))
    except KeyboardInterrupt:
        logging.info('\nClosing bot...')
        loop.run_until_complete(bot.close())
    finally:
        # cancel all lingering tasks
        loop.close()
        logging.info('\nBot has been deactivated.')
    return

if __name__ == '__main__':
    print(f'{__title__} v{__version__}\nProgrammed by {__author__}.')
    logging.basicConfig(level=logging.INFO)
    run()
    logging.shutdown()
