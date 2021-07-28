#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# StatusBot for Discord

"Status Bot for Discord using Python 3"

# Programmed by CoolCat467

__title__ = 'StatusBot'
__author__ = 'CoolCat467'
__version__ = '0.1.7'
__ver_major__ = 0
__ver_minor__ = 1
__ver_patch__ = 7

# https://discordpy.readthedocs.io/en/latest/index.html
# https://discord.com/developers

BOT_PREFIX = '!status'
OWNER_ID = 344282497103691777

from typing import Union

import os
import asyncio
import discord
##from discord.ext import tasks, commands
from dotenv import load_dotenv
import json
import random
import traceback
from threading import Event, Lock

# server_status is basically mcstatus from
# https://github.com/Dinnerbone/mcstatus
# with some slight modifications to make it better,
# expecially asyncronous stuff.
from status import server_status as mc

# Update talks to raw.githubusercontent.com.
import update

# Aquire token.
# Looks for file named ".env",
# file line 1 is "# .env",
# file line 2 is "DISCORD_TOKEN=XXXXX"
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Text globals
AZUP = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
AZLOW = AZUP.lower()
NUMS = '0123456789'


def writeFile(filename:str, data:str) -> None:
    "Write data to file <filename>."
    filename = os.path.abspath(filename)
    with open(filename, 'w', encoding='utf-8') as wfile:
        wfile.write(data)
        wfile.close()
    return

def appendFile(filename:str, data:str) -> None:
    "Add data to file <filename>."
    filename = os.path.abspath(filename)
    if os.path.exists(filename):
        with open(filename, 'a', encoding='utf-8') as wfile:
            wfile.write(data)
            wfile.close()
    else:
        writeFile(filename, data)
    return

def readFile(filename:str) -> Union[str, None]:
    "Read data from file <filename>. Return None if file does not exist."
    filename = os.path.abspath(filename)
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as rfile:
            data = rfile.read()
            rfile.close()
        return data
    return

def read_json(filename:str) -> Union[dict, None]:
    "Return json loads of filename read. Returns None if filename not exists."
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as rfile:
            try:
                data = json.load(rfile)
            except json.decoder.JSONDecodeError:
                return
            finally:
                rfile.close()
        return data
    return

def splitTime(seconds:int) -> list:
    "Split time into decades, years, months, weeks, days, hours, minutes, and seconds."
    seconds = int(seconds)
    def modTime(sec, num):
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
        t, seconds = modTime(seconds, num)
        ret.append(t)
    return ret

def combineAnd(data:list) -> str:
    "Join values of text, and have 'and' with the last one properly."
    data = list(data)
    if len(data) >= 2:
        data[-1] = 'and ' + data[-1]
    if len(data) > 2:
        return ', '.join(data)
    return ' '.join(data)

def printTime(seconds:int, singleTitleAllowed:bool=True) -> str:
    "Returns time using the output of splitTime."
    times = ('eons', 'eras', 'epochs', 'ages', 'millenniums',
             'centuries', 'decades', 'years', 'months', 'weeks',
             'days', 'hours', 'minutes', 'seconds')
    single = [i[:-1] for i in times]
    single[5] = 'century'
    split = splitTime(seconds)
    zipidxvalues = [(idx, split[idx]) for idx in range(len(split)) if split[idx]]
    if singleTitleAllowed:
        if len(zipidxvalues) == 1:
            index, value = zipidxvalues[0]
            if value == 1:
                return single[index]
    data = []
    for index, value in zipidxvalues:
        title = single[index] if abs(value) < 2 else times[index]
        data.append(str(value)+' '+title)
    return combineAnd(data)

def get_time_of_day(hour:int) -> str:
    "Figure out and return what time of day it is."
    if hour > 4 and hour < 12:
        return 'Morning'
    elif hour > 11 and hour < 19:
        # "It is usually from 12 PM to 6 PM,
        # but during winter it may be from 12 PM to 4 PM
        # and during summer it may be from 12 PM to 8 PM."
        return 'Afternoon'
    elif hour > 18 and hour < 22:
        return 'Evening'
    ##elif hour > 21 or hour < 4:
    return 'Night'

def exceptChars(text:str, valid:str=AZUP+AZLOW+NUMS+'.:-') -> str:
    "Return every character in text that is also in valid string."
    return ''.join(i for i in text if i in valid)

async def get_github_file(path:str, timeout:int=10) -> str:
    f"Return text from github file in {__title__} decoded as utf-8"
    file = await update.get_file(__title__, path, __author__, 'master', timeout)
    return file.decode('utf-8')

class Timer:
    "Class that will run coroutine self.run every delay secconds."
    delay = 60
    haultadd = 2
    def __init__(self, bot:discord.Client, delay:int) -> None:
        self.bot = bot
        self.delay = delay
        self.running = False
        self.stopped = False
        self.task = self.bot.loop.create_task(self.wait_for_ready_start())
        return
    
    async def hault(self) -> None:
        "Set self.running to False, cancel self.task, and wait for it to cancel completely."
        # Self.running is false now.
        self.running = False
        # Cancel task
        try:
            self.task.cancel()
        except:
            pass
        if not self.stopped:
            async def wait_for_canceled():
                while not self.task.cancelled():
                    await asyncio.sleep(0.1)
                return True
            self.stopped = await wait_for_canceled()
        return
    
    async def run(self) -> bool:
        "Return True."
        return True
    
    async def wait_for_ready_start(self) -> None:
        "Await self.bot.wait_until_ready(), then await self.start()."
        await self.bot.wait_until_ready()
        self.running = True
        await self.start()
        self.stopped = True
        return
    
    async def start(self) -> None:
        "Keep running self.run every self.delay seccond or until self.bot is closed or self.run returns True."
        while self.running:
            stop = await self.run()
            if stop or self.bot.is_closed():
                self.running = False
            else:
                await asyncio.sleep(self.delay)
        return
    pass

class GuildServerPinger(Timer):
    "Server pinger for guild."
    def __init__(self, bot:discord.Client, guildid:int) -> None:
        "Needs bot we work for, and id of guild we are pinging the server for."
        self.guildid = guildid
        self.server = mc.Server('')
        self.last_ping = set()
        self.last_json = {}
        self.last_delay = 0
        self.channel = None
        super().__init__(bot, 60)
        return
    
    async def run(self) -> bool:
        "Update server status. Return True if connection lost."
        try:
            json, ping = await self.server.async_status()
            self.last_json = json
            self.last_delay = ping
            current = []
            if 'players' in json:
                if 'sample' in json['players']:
                    for player in json['players']['sample']:
                        if 'name' in player:
                            current.append(player['name'])
            current = set(current)
            if current != self.last_ping:
                joined = tuple(current.difference(self.last_ping))
                left = tuple(self.last_ping.difference(current))
                
                delay = printTime(self.delay)
                def users_mesg(action:str, users:list) -> str:
                    "Return users {action} the server: {users}"
                    user = 'user' if len(users) == 1 else 'users'
                    text = f'The following {user} have {action} the server in the last {delay}:\n'
                    text += combineAnd([f'`{u}`' for u in users])
                    return text
                
                message = ''
                if left:
                    message += users_mesg('left', left)
                if joined:
                    if message:
                        message += '\n'
                    message += users_mesg('joined', joined)
                if message:
                    await self.channel.send(message)
            self.last_ping = current
        except Exception as ex:
            error = f'`A {type(ex).__name__} Error Has Occored'
            if ex.args:
                error += f': {", ".join(ex.args)}`'
            else:
                error += '.`'
            print(error)
            await self.channel.send(error)
            await self.channel.send('Connection to server has been lost.')
            return True
        return False
    
    async def start(self) -> None:
        "If config is good, run pinger."
        config = self.bot.get_guild_config(self.guildid)
        self.channel = self.bot.guess_guild_channel(self.guildid)
        if 'address' in config:
            self.server = mc.Server.lookup(config['address'])
            await super().start()
            await self.channel.send('Server pinger stopped.')
        else:
            await self.channel.send('No address for this guild defined, pinger not started.')
        return
    pass

class StatusBot(discord.Client):
    "StatusBot needs prefix, eventloop, and any arguments to pass to discord.Client."
    def __init__(self, prefix, *args, loop=asyncio.get_event_loop(), **kwargs):
        self.stopped = Event()
        self.updating = Lock()
        self.prefix = prefix
        self.loop = loop
        self.pingers = {}
        self.rootdir = os.path.split(os.path.abspath(__file__))[0]
        self.gcommands = {'currentversion': self.getcurrentvers,
                          'onlineversion': self.getonlinevers,
                          'getmyid': self.getmyid,
                          'getjson': self.getjson,
                          'getonline': self.getonline,
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
        super().__init__(*args, loop=self.loop, **kwargs)
        return
    
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
            writeFile(guildfile, '{}')
            guildconfig = {}
        return guildconfig
    
    def get_dm_config(self) -> dict:
        "Return a dictionary from the json read from the DMs config file."
        dmfile = self.get_dm_config_file()
        dmconfig = read_json(dmfile)
        if dmconfig is None:
            writeFile(dmfile, '{}')
            dmconfig = {}
        return dmconfig
    
    def write_guild_config(self, guildid:int, config:dict) -> None:
        "Write guild config file from config dictionary."
        guildfile = self.get_guild_config_file(guildid)
        writeFile(guildfile, json.dumps(config, indent=2))
        return
    
    def write_dm_config(self, config:dict) -> None:
        "Write DMs config file from config dictionary."
        dmfile = self.get_dm_config_file()
        writeFile(dmfile, json.dumps(config, indent=2))
        return
    
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
        coros = (guild.get_member_named(username) for guild in self.guilds)
        members = await asyncio.gather(*coros)
        for member in members:
            if not member is None:
                return member
        return
    
    async def add_guild_pinger(self, gid:int) -> str:
        "Create server pinger for guild if not exists. Return 'started', 'restarted', or 'none'."
        if not gid in self.pingers:
            self.pingers[gid] = GuildServerPinger(self, gid)
            return 'started'
        elif not self.pingers[gid].running:
            del self.pingers[gid]
            self.pingers[gid] = GuildServerPinger(self, gid)
            return 'restarted'
        return 'none'
    
    async def eval_guild(self, guildid:int) -> int:
        "Evaluate guild and it's config file and start pinger if able. Otherwise tell them to change settings."
        guildconfig = self.get_guild_config(guildid)
        channel = self.guess_guild_channel(guildid)
        if not 'channel' in guildconfig:
            await channel.send('This is where I will post leave-join messages until an admin sets my "channel" option.')
        if 'address' in guildconfig:
            action = await self.add_guild_pinger(guildid)
            if action != 'none':
                await channel.send(f'Server pinger {action}.')
        else:
            await channel.send(f'Server address not set, pinger not started. Please set it with "{self.prefix} setoption address <address>".')
        return guildid
    
    async def eval_guilds(self) -> list:
        "Evaluate all guilds. Return list of guild ids evaluated."
        coros = (self.eval_guild(guild.id) for guild in self.guilds)
        return await asyncio.gather(*coros)
    
    # Default, not affected by intents.
    async def on_ready(self) -> None:
        "Print information about bot and evaluate all guilds."
        print(f'{self.user} has connected to Discord!')
        print(f'Prefix: {self.prefix}')
        print(f'Intents: {self.intents}')
        print(f'Root Dir: {self.rootdir}')
        
        configdir = os.path.join(self.rootdir, 'config')
        if not os.path.exists(configdir):
            os.mkdir(configdir)
        guilddir = os.path.join(configdir, 'guilds')
        if not os.path.exists(guilddir):
            os.mkdir(guilddir)
        
        print(f'\n{self.user} is connected to the following guilds:\n')
        guildnames = []
        for guild in self.guilds:
            guildnames.append(f'{guild.name} (id: {guild.id})')
        c = max(len(name) for name in guildnames)
        print('\n'.join(n.center(c) for n in guildnames))
        await self.eval_guilds()
        act = discord.Activity(type=discord.ActivityType.watching, name=f'for {self.prefix}')
        await self.change_presence(status=discord.Status.online, activity=act)
        return
    
##    async def set_status(self, name:str) -> None:#, details:str) -> None:
##        "Set status of self."
##        print(f'Setting status to {name}')#: {details}')
####        atype = discord.ActivityType.custom
####        activity = discord.Activity(name=name, type=atype, details=details)
####        await self.change_presence(activity=activity)
##        #act = discord.Activity(name=name, details=details)
##        #act = discord.CustomActivity(name)#, details=details)
##        act = discord.Activity(type=discord.ActivityType.watching, name="a movie")
##        await self.change_presence(status=discord.Status.online, activity=act)
##        return
    
    async def getmyid(self, message) -> None:
        "Tell the author of the message their user id."
        await message.channel.send(f'Your user id is `{message.author.id}`.')
        return
    
    async def getjson(self, message) -> None:
        "Tell the author of the message the last json from server pinger."
        if message.guild.id in self.pingers:
            pinger = self.pingers[message.guild.id]
            lastdict = pinger.last_json
            msg = json.dumps(lastdict, sort_keys=True, indent=2)
            await message.channel.send(f'Last received json message:\n`{msg}`')
            #return await message.channel.send(f'Sent you a message as a dm.')
            return
        await message.channel.send('Server pinger is not running for this guild.')
        return
    
    async def getonline(self, message) -> None:
        "Tell the author of the message the usernames of the players currently connected to the guild's server."
        if message.guild.id in self.pingers:
            pinger = self.pingers[message.guild.id]
            players = list(pinger.last_ping)
            if players:
                players = [f'`{p}`' for p in players]
                await message.channel.send(f'Players online in last received sample:\n{combineAnd(players)}.')
                return
            await message.channel.send(f'No players were online in the last received sample.')
            return
        await message.channel.send('Server pinger is not running for this guild.')
        return
    
    async def stop(self, message) -> None:
        "Stop this bot. Sends stop message."
        config = self.get_dm_config()
        if not 'stopusers' in config:
            await message.channel.send(f'No one has permission to run this command.')
            return
        
        if message.author.id in config['stopusers']:
            await message.channel.send(f'Stopping...')
            # Set stopped event
            self.stopped.set()
            def close_bot():
                self.loop.create_task(self.close())
            self.loop.call_later(3, close_bot)
            return
        await message.channel.send(f'You do not have permission to run this command.')
        return
    
    async def getcurrentvers(self, message) -> tuple:
        "Get current version, tell user in message.channel, and return that version as tuple."
        await message.channel.send(f'Current version: {__version__}')
        return (__ver_major__, __ver_minor__, __ver_patch__)
    
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
            await message.channel.send(f'{__title__} is in the process of shutting down, canceling update.')
            return
        config = self.get_dm_config()
        if not 'updateusers' in config:
            await message.channel.send(f'No one has permission to run this command.')
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
                await message.channel.send(f'Retrieving file list...')
                try:
                    response = await get_github_file('files.json')
                    paths = tuple(update.get_paths(json.loads(response)))
                except:
                    # On failure, tell them we can't read file.
                    await message.channel.send('Could not read file list. Aborting update.')
                    self.updating.release()
                    return
                # Get max amount of time this could take.
                maxtime = printTime(timeout*len(paths))
                # Tell user number of files we are updating.
                if self.stopped.is_set():
                    await message.channel.send(f'{__title__} is in the process of shutting down, canceling update.')
                    self.updating.release()
                    return
                await message.channel.send(f'{len(paths)} files will now be updated. Please wait. This may take up to {maxtime} at most.')
                # Update said files.
                rootdir = os.path.split(self.rootdir)[0]
                await update.update_files(rootdir, paths, __title__, __author__, 'master', timeout)
                await message.channel.send('Done. Bot will need to be restarted to apply changes.')
                self.updating.release()
                return
            await message.channel.send(f'No update required.')
            self.updating.release()
            return
        await message.channel.send(f'You do not have permission to run this command.')
        return
    
    async def getoption_guild(self, message) -> None:
        "Send message with value of option given in this guild's config."
        args = message.content.split(' ')[2:]
        config = self.get_guild_config(message.guild.id)
        valid = tuple(config.keys())
        validops = combineAnd(f'`{opt}`' for opt in valid)
        validops = f' Valid options are: {validops}.
        if not args:
            await message.channel.send('Invalid option.'+validops)
            return
        option = args[0].lower()
        if option in valid:
            value = config[option]
            if isinstance(value, (list, tuple)):
                names = []
                for uid in value:
                    if isinstance(uid, int):
                        member = self.get_user(uid)
                        if not member is None:
                            name = member.name+'#'+member.discriminator
                            names.append(f'{name} (id. {uid})')
                        else:
                            names.append(str(uid))
                    else:
                        names.append(str(uid))
                value = ', '.join(names)
            await message.channel.send(f'Value of option "{option}": "{value}".')
            return
        await message.channel.send('Invalid option.'+validops)
        return
    
    async def getoption_dm(self, message) -> None:
        "Send message with value of option given in the dm config."
        args = message.content.split(' ')[1:]
        config = self.get_dm_config()
        valid = []
        if message.author.id == OWNER_ID:
            valid += ['setoptionusers', 'updateusers', 'stopusers']
        elif 'setoptionusers' in config:
            if message.author.id in config['setoptionusers']:
                valid += ['setoptionusers', 'updateusers', 'stopusers']
        validops = combineAnd(f'`{opt}`' for opt in valid)
        validops = f' Valid options are: {validops}.'
        if len(args) == 0:
            await message.channel.send('No option given.'+validops)
            return
        if valid:
            option = args[0].lower()
            if option in valid:
                value = config[option]
                if isinstance(value, (list, tuple)):
                    names = []
                    for uid in value:
                        if isinstance(uid, int):
                            member = self.get_user(uid)
                            if not member is None:
                                name = member.name+'#'+member.discriminator
##                                name = member.mention
                                names.append(f'`{name}` (id. `{uid}`)')
                            else:
                                names.append(f'`{uid}`')
                        else:
                            names.append(str(uid))
                    value = ', '.join(names)
                await message.channel.send(f'Value of option `{option}`: `{value}`.')
                return
            await message.channel.send('Invalid option.'+validops)
            return
        await message.channel.send(f'You do not have permission to view the values of any options.')
        return
    
    async def help_guild(self, message) -> None:
        "Send a message on message.channel telling user about all valid options."
        commands = '\n'.join('`'+k+'`' for k in (sorted(self.gcommands.keys(), reverse=True)))
        text = f"{__title__}'s Valid Guild Commands:\n{commands}"
        await message.channel.send(text)
        return
    
    async def help_dm(self, message) -> None:
        "Send a message on message.channel telling user about all valid options."
        commands = '\n'.join('`'+k+'`' for k in (sorted(self.dcommands.keys(), reverse=True)))
        text = f"{__title__}'s Valid DM Commands:\n{commands}"
        await message.channel.send(text)
        return
    
    async def refresh(self, message) -> None:
        "Re-evaluate guild, then tell them it happened."
        await self.eval_guild(message.channel.guild.id)
        await message.channel.send(f'Guild has been re-evaluated.')
        return
    
    # @commands.has_permissions(administrator=True, manage_messages=True, manage_roles=True)
    async def setoption_guild(self, message) -> None:
        "Set a config option. Send message in message.channel on falure."
        args = message.content.split(' ')[2:]
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
        
        validops = combineAnd(f'`{opt}`' for opt in valid)
        validops = f' Valid options are: {validops}.'
        
        if not valid:
            args = []
        
        if args:
            option = args[0].lower()
            if option in valid:
                if len(args) < 2:
                    msg = f'Insufficiant arguments for {option}.'
                    arghelp = {'address': 'Server address of a java edition minecraft server.',
                               'channel': 'Name of the discord channel to send join-leave messages to.',
                               'setoptionusers': '`clear`, a discord id, or the username of a new user to add to the permission list.'}
                    msg += '\nArgument required: '+arghelp[option]
                    await message.channel.send(msg)
                    return
                value = exceptChars(args[1], AZUP+AZLOW+NUMS+'.:-#')
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
                            uid = int(value)
                        except ValueError:
                            # DANGER
                            if not '#' in args[1]:
                                await message.channel.send('Username does not have discriminator (ex. #1234).')
                                return
                            member = message.guild.get_member_named(args[1])
                            if member is None:
                                await message.channel.send('User not found / User not in this guild.')
                                return
                            value = member.id
                        member = message.guild.get_member(value)
##                        member = self.get_user(value)
                        if member is None:
                            await message.channel.send('User not found / User not in this guild.')
                            return
                        name = member.name+'#'+member.discriminator
##                        name = member.mention
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
                await self.refresh(message)
                return
        if valid:
            await message.channel.send('Invalid option.'+validops)
            return
        await message.channel.send('You do not have permission to set any options. If you feel this is a mistake, please contact server admin(s) and have them give you permission.')
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
        
        validops = combineAnd(f'`{opt}`' for opt in valid)
        validops = f' Valid options are: {validops}.'
        
        args = message.clean_content.split(' ')[1:]
        if args:
            option = args[0].lower()
            
            if option in valid:
                if len(args) < 2:
                    msg = f'Insufficiant arguments for {option}.'
                    arghelp = {'stopusers': '`clear`, a discord user id, or the username of a new user to add to the permission list of users who can stop the bot.',
                               'updateusers': '`clear`, a discord user id, or the username of a new user to add to the permission list of users who can update the bot.',
                               'setoptionusers': '`clear`, a discord user id, or the username of a new user to add to the permission list of users who can change the stop and update permissions of the bot.'}
                    msg += '\nArgument required: '+arghelp[option]
                    await message.channel.send(msg)
                    return
                value = args[1]
                if value.lower() == 'clear':
                    value = []
                else:
                    try:
                        uid = int(value)
                    except ValueError:
                        # DANGER
                        if not '#' in args[1]:
                            await message.channel.send('Username does not have discriminator (ex. #1234).')
                            return
                        member = await self.search_for_member_in_guilds(value)
                        if member is None:
                            await message.channel.send('User not found.')
                            return
                        value = member.id
                    member = self.get_user(value)
                    if member is None:
                        await message.channel.send('User not found.')
                        return
                    name = member.name+'#'+member.discriminator
##                    name = member.mention
                    value = [value]
                    if option in config:
                        if value[0] in config[option]:
                            await message.channel.send(f'User `{name}` (id `{value[-1]}`) already in this list!')
                            return
                        value = config[option]+value
                    await message.channel.send(f'Adding user `{name}` (id `{value[-1]}`)')
                config[option] = value
                self.write_dm_config(config)
                await message.channel.send(f'Updated value of option `{option}` to `{value}`.')
                return
        if valid:
            await message.channel.send('Invalid option.'+validops)
            return
        await message.channel.send('You do not have permission to set any options.')
        return
    
    async def process_command_message(self, message, mode:str):
        "Process new command message. Calls self.command[command](message)."
        if self.stopped.is_set():
            await message.channel.send(f'{__title__} is in the process of shutting down.')
        err = ' Please enter a valid command. Use "`{}help`" to see valid commands.'
        # 1 if it's guild, 0 if dm.
        midx = int(mode == 'guild')
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
                await message.channel.send('Command not found.'+err)
                return
            # Prefix doesn't have to be there in dm, so add space so args works right.
            content += ' '
        args = content.split(' ')
        # Get command. zeroth if dm, first if guild because of prefix.
        command = args[midx].lower()
        # If command is valid, run it.
        if command in commands:
            await commands[command](message)
            return
        if not midx and content.startswith(self.prefix):
            await message.channel.send("When you talk to me in DMs, you don't have to start with my prefix for me to react!")
            return
        # Otherwse, send error of no command.
        await message.channel.send('No command given.'+err)
        return
    
    # Intents.guilds
    async def on_guild_join(self, guild) -> None:
        "Evaluate guild."
        await self.eval_guild(guild.id)
        return
    
    # Intents.members
    async def on_member_join(self, member) -> None:
        pass
    
    # Intents.members
    async def on_member_remove(self, member) -> None:
        pass
    
    # Intents.guilds
    async def on_guild_remove(self, guild) -> None:
        "Remove config file for guild we are no longer in."
        os.remove(self.get_guild_config_file(guild.id))
        return
    
    # Intents.dm_messages, Intents.guild_messages, Intents.messages
    async def on_message(self, message) -> None:
        "React to any new messages."
##        print(message.clean_content, message.content)
        # Don't process anything if the bot is shutting down.
        if self.stopped.is_set():
            return
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
            return
        # can't send messages so skip.
        return
    
    # Default, not affected by intents
    async def on_error(self, event, *args, **kwargs) -> None:
        "Log error and continue."
        if event == 'on_message':
            print(f'Unhandled message: {args[0]}')
        # Get values from exc_info
        values = os.sys.exc_info()
        # Get log path
        logpath = os.path.join(self.rootdir, 'log.txt')
        # Get error message.
        msg = '#'*8+'\n'+'Error Event:\n'+str(event)+'\n'
        msg += 'Exception class:\n'+str(values[0])+'\n'
        msg += 'Exception text:\n'+str(values[1])+'\n'
        msg += 'Error args:\n'+'\n'.join(map(str, args))+'\n'
        msg += 'Error kwargs:\n'
        msg += '\n'.join(f'{key}:{kwargs[key]}' for key in kwargs)+'\n'
        class fakefile:
            def __init__(self):
                self.data = []
            def write(self, value):
                self.data.append(value)
            def getdata(self):
                return ''.join(self.data)[:-1]
            pass
        yestotalyafile = fakefile()
        traceback.print_exception(None, values[1],
                                  values[2],
                                  file=yestotalyafile)
        msg += 'Traceback:\n'+yestotalyafile.getdata()+'\n'
        msg += '#'*8
        print(msg)
        appendFile(logpath, msg)
        return
    
    # Default, not affected by intents
    async def close(self) -> None:
        "Tell guilds bot shutting down."
        self.stopped.set()
        print('\nShutting down pingers.\n')
        async def stop_pinger(guild):
            if guild.id in self.pingers:
                print(f'Waiting for {guild.name}\'s pinger to stop...')
                await self.pingers[guild.id].hault()
                print(f'{guild.name}\'s pinger stopped.')
        coros = (stop_pinger(guild) for guild in self.guilds)
        await asyncio.gather(*coros)
        print('\nPingers shut down...\n')
        
        print('Telling guilds bot is shutting down.\n')
        async def tell_guild_shutdown(guild):
            channel = self.guess_guild_channel(guild.id)
            await channel.send(f'{__title__} is shutting down.')
            return
        coros = (tell_guild_shutdown(guild) for guild in self.guilds)
        await asyncio.gather(*coros)
        
        print('Waiting to aquire updating lock...\n')
        self.updating.acquire()
        print('Closing...')
        await super().close()
        self.updating.release()
        return
    pass

def run() -> None:
    "Run bot."
    global bot
    if TOKEN is None:
        print('\nNo token set!\nEither add ".env" file in bots folder with DISCORD_TOKEN=<token here> line,\nor set DISCORD_TOKEN environment variable.')
        return
    print('\nStarting bot...')
    
    loop = asyncio.get_event_loop()
    intents = discord.Intents()
    intents.dm_messages = True
    intents.guild_messages = True
    intents.messages = True
    intents.guilds = True
    intents.members = True
    # 4867
    
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
    print('%s v%s\nProgrammed by %s.' % (__title__, __version__, __author__))
    run()
