#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# StatusBot for Discord

"""Status Bot for Discord using Python 3"""

# Programmed by CoolCat467

__title__ = 'StatusBot'
__author__ = 'CoolCat467'
__version__ = '0.0.6'
__ver_major__ = 0
__ver_minor__ = 0
__ver_patch__ = 6

# https://discordpy.readthedocs.io/en/latest/index.html
# https://discord.com/developers

BOT_PREFIX = '!status'
OWNER_ID = 344282497103691777

import os
import asyncio
import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
import json
import random

# server_status is basically mcstatus from
# https://github.com/Dinnerbone/mcstatus
# with some slight modifications to make it better,
# expecially asyncronous stuff.
import server_status as mc

# Update talks to raw.githubusercontent.com.
import update

# Aquire token.
# Looks for file named ".env",
# file line 1 is "# .env",
# file line 2 is "DISCORD_TOKEN=XXXXX"
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# intents = discord.Intents(messages=True,
#                           guilds=True,
#                           status=True)

def writeFile(filename, data):
    "Write data to file."
    filename = os.path.abspath(filename)
    with open(filename, 'w', encoding='utf-8') as wfile:
        wfile.write(data)
        wfile.close()
    return

def appendFile(filename, data):
    "Add data to file."
    filename = os.path.abspath(filename)
    if os.path.exists(filename):
        with open(filename, 'a', encoding='utf-8') as wfile:
            wfile.write(data)
            wfile.close()
    else:
        writeFile(filename, data)
    return

def readFile(filename):
    "Read data from file."
    filename = os.path.abspath(filename)
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as rfile:
            data = rfile.read()
            rfile.close()
        return data
    return ''

def read_json(filename):
    "Return json loads of filename read. Returns None if filename not exists."
    if os.path.exists(filename):
        return json.loads(readFile(filename))
    return

def exceptChars(text, valid='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.0123456789-:'):
    "Return every character in text that is also in valid string."
    return ''.join(i for i in text if i in valid)

async def get_github_file(loop, path):
    data = await update.get_file(loop, __title__, path)
    return data.decode('utf-8')

# https://gist.github.com/akaIDIOT/48c2474bd606cd2422ca
def call_periodic(loop, interval, function, onexit=lambda:None, *args):
    "Return PeriodicHandle to call function soon with loop every interval. If function returns False, loop will stop and onexit will be called. Function called with *args."
    # record the loop's time when call_periodic was called
    start = loop.time()
    
    def run(handle):
        # XXX: we could record before = loop.time() and warn when callback(*args) took longer than interval
        # call callback now (possibly blocks run)
        come_back = function(*args)
        # reschedule run at the soonest time n * interval from start
        # re-assign delegate to the new handle
        if come_back:
            handle.delegate = loop.call_later(interval - ((loop.time() - start) % interval), run, handle)
        else:
            onexit()
            handle.cancel()
    
    class PeriodicHandle:  # not extending Handle, needs a lot of arguments that make no sense here
        def __init__(self):
            self.delegate = None
            self.canceled = False

        def cancel(self):
            if isinstance(self.delegate, asyncio.Handle):
                if not self.canceled:
                    self.delegate.cancel()
            self.canceled = True
        pass
    
    periodic = PeriodicHandle()  # can't pass result of loop.call_at here, it needs periodic as an arg to run
    # set the delegate to be the Handle for call_at, causes periodic.cancel() to cancel the call to run
    periodic.delegate = loop.call_at(start + interval, run, periodic)
    # return the 'wrapper'
    return periodic

class ProcessGuild():
    ping_delay = 60
    def __init__(self, bot, guildid):
        self.bot = bot
        self.guildid = guildid
        self.server = mc.Server('')
        self.last_ping = set()
        self.last_json = {}
        self.last_delay = 0
        self.periodic = None
        self.bot.loop.call_soon(self.setup_server)
        self.come_back = True
        return
    
    def call_async(self, coro):
        "Create a new task to run coroutine in self.bot.loop."
        return self.bot.loop.create_task(coro)
    
    def update(self, *args, **kwargs):
        "Setup self.asyncupdate task to run."
        self.call_async(self.asyncupdate(*args, **kwargs))
        return self.come_back
    
    async def asyncupdate(self, close):
        "Update server status."
        if close or not self.come_back:
            print('Closing')
            self.come_back = False
            return False
        channel = self.bot.get_channel(self.channelid)
        try:
            json, ping = await self.server.async_status()
            self.last_json = json
            self.last_delay = ping
            current = []
            if 'players' in json:
                if 'sample' in json['players']:
                    current = [player['name'] for player in json['players']['sample']]
            
            current = set(current)
            if current != self.last_ping:
                joined = tuple(current.difference(self.last_ping))
                left = tuple(self.last_ping.difference(current))
                
                message = ''
                if left:
                    message += f'The following user(s) have left the server in the last {self.ping_delay} secconds:\n'
                    message += ', '.join(left[:-1])+('and '+left[-1] if len(left) > 1 else left[-1])
                    if joined:
                        message += '\n'
                if joined:
                    message += f'The following user(s) have joined the server in the last {self.ping_delay} secconds:\n'
                    message += ', '.join(joined[:-1])+('and '+joined[-1] if len(joined) > 1 else joined[-1])
                if message:
                    await channel.send(message)
            self.last_ping = current
        except Exception as ex:
            error = f'A {type(ex).__name__} Error Has Occored: {", ".join(ex.args)}'
            print(error)
            await channel.send(error)
            await channel.send('Connection to server has been lost. No longer monitoring server.')
            self.come_back = False
            return False
        self.come_back = True
        return True
    
    def hault(self):
        "Delete pinger and tell channel pinger stopped."
        self.periodic.cancel()
        if self.guildid in self.bot.pingers:
            del self.bot.pingers[self.guildid]
        channel = self.bot.get_channel(self.channelid)
        self.call_async(channel.send('Server pinger stopped.'))
        pass
    
    def setup_server(self):
        "Setup update to be called periodically if config is good."
        config = self.bot.get_guild_config(self.guildid)
        channel = self.bot.guess_guild_channel(self.guildid)
        self.channelid = channel.id
        if 'address' in config:
            self.server = mc.Server.lookup(config['address'])
            self.periodic = call_periodic(self.bot.loop, self.ping_delay, self.update, self.hault, not self.bot.is_closed)
        return
    pass

class StatusBot(discord.Client):
    def __init__(self, prefix, eventloop, *args, **kwargs):
        self.prefix = prefix
        self.loop = eventloop
        self.pingers = {}
        self.rootdir = os.path.split(__file__)[0]
        self.commands = {'getmyid': self.getmyid,
                         'getjson': self.getjson,
                         'stop': self.stop,
                         'update': self.update,
                         'refresh': self.refresh,
                         'setoption': self.setoption,
                         'getoption': self.getoption,
                         'help': self.help}
        super().__init__(*args, **kwargs)
        return
    
    def get_guild_config_file(self, guildid:int) -> str:
        "Return the path to the config json file for a ceartain guild id."
        return os.path.join(self.rootdir, 'config', str(guildid)+'.json')
    
    def get_guild_config(self, guildid:int) -> dict:
        "Return a dictionary from the json read from guild config file."
        guildfile = self.get_guild_config_file(guildid)
        guildconfig = {}
        if os.path.exists(guildfile):
            # Guild has config saved.
            guildconfig = read_json(guildfile)
        else:
            # Guild does not have config
            # Therefore, create file for them
            writeFile(guildfile, json.dumps({}))
        return guildconfig
    
    def write_guild_config(self, guildid:int, config:dict) -> None:
        "Write guild config file from config dictionary."
        guildfile = self.get_guild_config_file(guildid)
        writeFile(guildfile, json.dumps(config))
        return
    
    def guess_guild_channel(self, guildid:int):
        "Guess guild channel and return channel."
        guild = self.get_guild(guildid)
        config = self.get_guild_config(guildid)
        valid = [chan.name for chan in guild.text_channels]
        if 'channel' in config:
            channelname = config['channel']
            if channelname in valid:
                channel = discord.utils.get(guild.text_channels, name=channelname)
                return channel
        expect = [cname for cname in valid if 'bot' in cname.lower()]+['general']
        for channel in guild.text_channels:
            if channel.name in expect:
                return channel
        channelname = random.choice(valid)
        return discord.utils.get(guild.text_channels, name=channelname)
    
    async def eval_guild(self, guild):
        "Evaluate guild and it's config file and start pinger if able. Otherwise tell them to change settings."
        guildconfig = self.get_guild_config(guild.id)
        channel = self.guess_guild_channel(guild.id)
        if not 'channel' in guildconfig:
            await channel.send('This is where I will post leave-join messages until somone sets my "channel" option.')
##        else:
##            await channel.send('Restarting...')
        if 'address' in guildconfig:
            if not guild.id in self.pingers:
                self.pingers[guild.id] = ProcessGuild(self, guild.id)
                await channel.send('Server pinger started.')
            elif self.pingers[guild.id].canceled:
                try:
                    self.pingers[guild.id].cancel()
                except:
                    pass
                del self.pingers[guild.id]
                self.pingers[guild.id] = ProcessGuild(self, guild.id)
                await channel.send('Server pinger restarted.')
        else:
            await channel.send(f'Server address not set, pinger not started. Please set it with "{self.prefix} setoption server <address>".')
        return
    
    async def eval_guilds(self):
        "Evaluate all guilds."
        coros = [self.eval_guild(guild) for guild in self.guilds]
        return await asyncio.gather(*coros, loop=self.loop)
    
    async def on_ready(self):
        "Print information about bot and evaluate all guilds."
        print(f'{self.user} has connected to Discord!')
        print(f'Prefix: {self.prefix}')
        print(f'Intents: {self.intents}')
        
        configdir = os.path.join(self.rootdir, 'config')
        if not os.path.exists(configdir):
            os.mkdir(configdir)        
        
        for guild in self.guilds:
            print(
                f'\n{self.user} is connected to the following guild:\n'
                f'{guild.name}(id: {guild.id})'
            )
        await self.eval_guilds()
        return
    
    async def set_status(self, name, details):
        "Set status of self."
        print(f'Setting status to {name}: {details}')
        atype = discord.ActivityType.custom
        activity = discord.Activity(name=name, type=atype, details=details)
        await self.change_presence(activity=activity)
        return

    async def getmyid(self, message):
        "Tell the author of the message their user id."
        return await message.channel.send(f'Your user id is "{message.author.id}".')

    async def getjson(self, message):
        "Tell the author of the message the last json from server pinger."
        if message.guild.id in self.pingers:
            pinger = self.pingers[message.guild.id]
            lastdict = pinger.last_json
            msg = json.dumps(lastdict, sort_keys=True, indent=2)
            return await message.channel.send(f'Last received json message:\n{msg}')
            #return await message.channel.send(f'Sent you a message as a dm.')
        return await message.channel.send('Server pinger is not running.')
    
    async def stop(self, message):
        "Stop this bot."
        config = self.get_guild_config(message.guild.id)
        if 'stopusers' in config:
            if message.author.id in config['stopusers']:
                await message.channel.send(f'Stopping...')
                await self.close()
            return await message.channel.send(f'You not have privileges to run this command.')
        return await message.channel.send('No one in this guild has permission to run this command.')
    
    async def update(self, message):
        "Preform update from github."
        config = self.get_guild_config(message.guild.id)
        if 'updateusers' in config:
            if message.author.id in config['updateusers']:
                await message.channel.send('Retrieving version from github...')
                version = await get_github_file(self.loop, 'version.txt')
                vertext = f'Current: v{__version__}\nOnline: v{version}'
                await message.channel.send(vertext)
                newvers = map(int, version.split('.'))
                curvers = (__ver_minor__, __ver_minor__, __ver_patch__)
                less = lambda x, y:x<y
                if any((less(*xy) for xy in zip(curvers, newvers))):
                    async def update_file(fname, gitpath):
                        data = await get_github_file(self.loop, gitpath)
                        filename = os.path.join(self.rootdir, fname)
                        writeFile(filename, data)
                    await message.channel.send(f'Retrieving file list...')
                    files = await get_github_file(self.loop, 'files.json')
                    files = json.loads(files)
                    count = len(tuple(set(files.keys())))
                    await message.channel.send(f'{count} files will now be updated. Please wait.')

                    coros = [update_file(key, files[key]) for key in files]
                    await asyncio.gather(*coros, loop=self.loop)
                    return await message.channel.send('Done. Bot will need to be restarted to apply changes.')
                return await message.channel.send(f'No update required.')
            return await message.channel.send(f'You not have privileges to run this command.')
        return await message.channel.send('No one in this guild has permission to run this command.')
    
    async def getoption(self, message):
        "Send message with value of option given in this guild's config."
        args = message.content.split(' ')[2:]
        config = self.get_guild_config(message.guild.id)
        valid = tuple(config.keys())
        if len(args) == 0:
            return await message.channel.send(f"No option given. Valid options are: {', '.join(valid)}.")
        option = args[0].lower()
        if option in valid:
            return await message.channel.send(f'Value of option "{option}": "{config[option]}".')
        return await message.channel.send(f"Invalid option. Valid options are: {', '.join(valid)}.")
    
    async def help(self, message):
        "Send a message on message.channel telling user about all valid options."
        commands = '\n'.join(sorted(self.commands.keys(), reverse=True))
        text = f"{__title__}'s Valid Commands:\n{commands}"
        return await message.channel.send(text)
    
    async def refresh(self, message):
        "Re-evaluate guild, then tell them it happened."
        await self.eval_guild(message.channel.guild)
        return await message.channel.send(f'Guild has been re-evaluated.')
    
    # @commands.has_permissions(administrator=True, manage_messages=True, manage_roles=True)
    async def setoption(self, message):
        "Set a config option. Send message in message.channel on falure."
        args = message.content.split(' ')[2:]
        config = self.get_guild_config(message.guild.id)
        valid = ['address', 'channel']
        
        if message.author.id == OWNER_ID:
            valid += ['setoptionusers', 'updateusers', 'stopusers']
        elif 'setoptionusers' in config:
            if message.author.id in config['setoptionusers']:
                valid += ['setoptionusers', 'updateusers', 'stopusers']
        
        if len(args) == 0:
            return await message.channel.send(f"No option given. Valid options are: {', '.join(valid)}.")
        option = args[0].lower()
        if option in valid:
            if len(args) < 2:
                msg = f'Insufficiant arguments for {option}.'
                arghelp = {'address': 'Address java MC server accessable at.',
                           'channel': 'Name of the discord channel to send join-leave messages to.',
                           'setoptionusers': 'List of user ids that can set advanced options using this command.',
                           'updateusers': 'List of user ids that can preform the update command.',
                           'stopusers': f'List of user ids that can shut down {__title__}.'}
                msg += '\nArgument required: '+arghelp[option]
                return await message.channel.send(msg)
            value = exceptChars(args[1])
            if option == 'channel':
                channelnames = [chan.name for chan in message.guild.text_channels]
                if not value in channelnames:
                    return await message.channel.send('Channel not found.')
            if option in ('setoptionusers', 'updateusers', 'stopusers'):
                if value == 'clear':
                    value = []
                else:
                    try:
                        value = [int(value)]
                    except TypeError:
                        return await message.channel.send('Invalid value. ID must be an intiger.')
                    if option in config:
                        if value[0] in config[option]:
                            return await message.channel.send('User ID already in this list!')
                        value += config[option]
            config[option] = value
            self.write_guild_config(message.channel.guild.id, config)
            await message.channel.send(f'Updated value of option "{option}" to "{value}".')
            await self.eval_guild(message.channel.guild)
            return await message.channel.send(f'Guild has been re-evaluated.')
            # return await self.refresh(message)
        return await message.channel.send(f"Invalid option. Valid options are: {', '.join(valid)}.")
    
    async def process_command_message(self, message):
        "Process new command message. Calls self.command[command](message)."
        err = f' Please enter a valid command. Use "{self.prefix} help" to see valid commands.'
        content = message.content
        if ' ' in content:
            args = content.split(' ')[1:]
            command = args[0].lower()
            if command in self.commands:
                return await self.commands[command](message)
            return await message.channel.send('Command not found.'+err)
        return await message.channel.send('No command given.'+err)
    
    async def on_guild_join(self, guild):
        "Evaluate guild."
        return await self.eval_guild(guild)
    
    async def on_guild_remove(self, guild):
        "Remove config file for guild we are no longer in."
        os.remove(self.get_guild_config_file(guild.id))
        return
    
    async def on_message(self, message):
        "React to any new messages."
        # Skip messages from ourselves.
        if message.author == self.user:
            return
        
        if hasattr(message.channel, 'send'):
            if hasattr(message.guild, 'id'):
                msg = message.content
                if msg.lower().startswith(self.prefix):
                    return await self.process_command_message(message)
                return
            return await message.channel.send(f'{__title__} does not support non-guild channels.')
        return
    
    async def on_error(self, event, *args, **kwargs):
        "Log error and continue."
        if event == 'on_message':
            print(f'Unhandled message: {args[0]}')
        values = os.sys.exc_info()
        logpath = os.path.join(self.rootdir, 'log.txt')
        msg = '\n'.join(map(str, values))
        msg = '#'*8+'\n'+'Error Event:\n'+str(event)+'\n'+msg+'\n'+'#'*8
        appendFile(logpath, msg)
        return
    
    async def close(self):
        "Tell guilds bot shutting down."
        print('Shutting down pingers.')
        async def stop_pinger(guild):
            if guild.id in self.pingers:
                #pinger = self.pingers[guild.id]
                #if not pinger.periodic.canceled:
                pinger.hault()
        coros = [stop_pinger(guild) for guild in self.guilds]
        await asyncio.gather(*coros, loop=self.loop)
        print('Pingers shut down...')
        
        print('Telling guilds bot is shutting down.')
        async def tell_guild_shutdown(guild):
            channel = self.guess_guild_channel(guild.id)
            return await channel.send(f'{__title__} shutting down.')
        coros = [tell_guild_shutdown(guild) for guild in self.guilds]
        await asyncio.gather(*coros, loop=self.loop)
        print('Closing...')
        await super().close()
        return
    pass

def run():
    print('\nStarting bot...')
    
    #discord.Intents.guilds
    loop = asyncio.get_event_loop()
    bot = StatusBot(BOT_PREFIX, loop, loop=loop)
    
    try:
        loop.run_until_complete(bot.start(TOKEN))
    except KeyboardInterrupt:
        print('Closing bot...')
        loop.run_until_complete(bot.close())
        # cancel all lingering tasks
    finally:
        loop.close()
    print('Bot has been deactivated.')

if __name__ == '__main__':
    print('%s v%s\nProgrammed by %s.' % (__title__, __version__, __author__))
    run()
