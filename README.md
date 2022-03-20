# StatusBot
StatusBot is a discord bot that will post information about a given Java Editon minecraft server in a given channel once configured.


## Invite to your server
Invite StatusBot to your discord server:
[Invite link](https://discord.com/api/oauth2/authorize?client_id=859890649535873044&permissions=68608&scope=bot)
Note, there may be random downtimes if problems occour, and because of the nature of
this bot whoever runs the bot will have access to the address of your minecraft server and
the name of the channel the bot will be sending messages in.
Prevent random people from joining your minecraft server by setting up a whitelist.


## Installation
For Fresh install use this command:
`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/CoolCat467/StatusBot/HEAD/install.sh)"`

For update installation use this command:
`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/CoolCat467/StatusBot/HEAD/install_update.sh)"`


## Usage
As far as I can tell, StatusBot only needs the following permissions intiger: `68608`
If you preform a fresh install, you will need to set the discord token the bot will use.
The program looks for this token in a file named `.env`. If you use the fresh installer,
the installer will automatically create this file and open it with `nano` for you to paste
your token. If you use the update installer, it will move the old version to `old` and copy
the old `.env` to the new folder.

At the moment, StatusBot must install in `~/Desktop/Bots/StatusBot`. This will
probably change in the future because that's a bit of an odd limitation, don't
you think? If you absolutely must change the install directory, run `create_installers.sh`.
This will likely become a built-in part of installing StatusBot in the future.

In both installation cases, `looprun.sh` will be run, which will start the bot and restart
it in the event of a critical error.

Every time after you install the bot, all you have to do is run `looprun.sh` or just
`run.sh`. Looprun will simply call the run script, and then re-call itself.

In the event of an error, information about the error is stored in `log.txt` in StatusBot's
folder.

## Using this bot
StatusBot's command prefix is, on default, `!status`. The actual capitalization of
most commands does not matter. StatusBot should respond to the user in the channel
they entered the command in, except in the case that the channel does not support
being written to.

## Commands
As of version 0.4.0, the following describes StatusBot's commands.

### In Guilds:
`help` - Display all of StatusBot's valid guild commands.

`refresh [force]` - Refresh, or re-evaluate, the guild that the command message is sent in.
 Restarts server pinger if guild `address` value is set.
 
 If 'force' is given as an additional argument and user is either
 the guild owner, StatusBot's owner, or a user in the `forcerefreshusers` list,
 then you can force the guild server pinger to restart. Otherwise it only restarts if
 it needs too.

`setoption <name> <value>` - Set option <name> to <value> for the guild you are currently
  talking to StatusBot in.
   
  If you are StatusBot's owner, you are the guild owner, or you are in the
  `setoptionusers` list, the following settings can be modified:
  
   `address` - Address of the java editon minecraft server StatusBot should monitor
   
   `channel` - Name of the discord channel StatusBot should post player leave-join messages in.
   
   `forcerefreshusers` - List of user IDs able to preform a force refresh.
  
  If you are either StatusBot's owner or you are the guild owner, you modify the
  `setoptionusers` list.
  
  All of the following options take 'clear', a user id, or a username (including discriminator),
  to add to list as an argument.
  
   `setoptionusers` - List of user IDs able to modify `address` and `channel` values.

`getoption <name>` - Tell you the value of option <name>. Anyone can retrieve any option.

`getmyid` - Tell the user who sent the message what their unique discord id is.

`getjson` - Tell the user who sent the message the last json received from pinging the server.

`getonline` - Tell the user who sent the message the last received list of known online players.

`getping` - Tell the user who sent the message the latency of the connection to the server.

`getfavicon` - Post a picture of the server's favicon in the channel the command message was posted in.
 
`currentversion` - Tell the user the current version of StatusBot.

`onlineversion` - Tell the user the current online verison of StatusBot.
This value is controlled by `version.txt` in this repository.


### In a DM:
`help` - Display all of StatusBot's valid DM commands.

`setoption <name> <value>` - Set global dm option <name> to <value>

 All of the following options take 'clear', a user id, or a username (including discriminator),
 to add to list as an argument.
 
   `setoptionusers` - List of users who can modify the `updateusers` and `stopusers` lists.

  NOTE: This option can only be set by the bot owner.

   The following two options can only be set by users in the `setoptionusers` list.

   `updateusers` - List of users who can run the `update` dm command

   `stopusers` - List of users who can run the `stop` dm command

`getoption <name>` - Get global dm option <name>

 getoption in a dm is a bit different than it's counterpart in guild commands.
 This version of getoption will only tell the user the values of the given option
 if they are either the bot owner or in the `setoptionusers` list.

`stop` - Stop the bot. If `looprun.sh` was used, this has the effect of restarting the bot.
  
  NOTE: This command will only work if you are in the `stopusers` list in the
  global dms config file.

`update` - Attempt to update the bot to the newest version using this github repository.
  
  NOTE: This command is nearly identically to the `stop` dm command, but uses the
  `updateusers` global dm config value instead.

`getmyid` - Tell the user who sent the message what their unique discord id is.

`currentversion` - Tell the user the current version of StatusBot.

`onlineversion` - Tell the user the current online verison of StatusBot.
This value is controlled by `version.txt` in this repository.


## Automatic messaging
When StatusBot is connected to a guild and has it's `address` (and preferably also it's `channel`)
value set, StatusBot will go to the channel defined by the `channel` option (if unset, goes to first
any channels with `bot` in the title, then `general`, and if that fails then a random text channel)
and post the following message: `Server pinger started.` As long as the pinger is running every 60
secconds (on default) StatusBot will connect to and ping the server found at `address` and see if
any players have joined or left since the last time it pinged said server. If any players have
joined or left the server, StatusBot will tell you!


## Credits
Most of the stuff to talk to minecraft server stolen from https://github.com/Dinnerbone/mcstatus with
some changes.
Parts of code stolen from WOOF (Web Offer One File) from https://github.com/simon-budig/woof
