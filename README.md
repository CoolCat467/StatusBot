# StatusBot
StatusBot is a discord bot that will post information about a given Java Editon minecraft server in a given channel once configured.


## Installation
For Fresh install use this command:
`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/CoolCat467/StatusBot/HEAD/install.sh)"`

For update installation use this command:
`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/CoolCat467/StatusBot/HEAD/install_update.sh)"`


## Usage
If you preform a fresh install, you will need to set the discord token the bot will use.
The program looks for this token in a file named `.env`. If you use the fresh installer,
the installer will automatically create this file and open it with `nano` for you to paste
your token. If you use the update installer, it will move the old version to `old` and copy
the old `.env` to the new folder.

In both installation cases, `looprun.sh` will be run, which will start the bot and restart
it in the event of a critical error.

Every time after you install the bot, all you have to do is run `looprun.sh` or just
`run.sh`. Looprun will simply call the run script, and then re-call itself.

In the event of an error, information about the error is stored in `log.txt` in StatusBot's
folder.

## Using this bot
StatusBot's command prefix is, on default, `!StatusBot`. The actual capitalization of
most commands does not matter. StatusBot should respond to the user in the channel
they entered the command in, except in the case that the channel does not support
being writen to.

## Commands
As of v0.0.4, these are the following commands:
`help` - Display all valid commands.
`setoption <name> <value>` - Set option <name> to <value> for the guild you are currently
  talking to StatusBot in. Current settable options as of v0.0.4:
   `address` - Address of the java editon minecraft server StatusBot should monitor
   `channel` - Name of the discord channel StatusBot should post player leave-join messages in.
  If your id is the same as OWNER_ID or your id is in `setoptionusers`, more options are available.
  All of the following options take 'clear' or a user id to add to list as an argument.
   `setoptionusers` - List of user IDs able to modify more advanced settings.
   `updateusers` - List of user IDs able to run the update command.
   `stopusers` - List of user IDs able to stop the bot.
`getoption <name>` - Tell you the value of option <name>.
`getmyid` - Tell the user who sent the message what their unique discord id is.
`stop` - Stop the bot. If `looprun.sh` was used, this has the effect of restarting the bot.
  NOTE: This command will only work if the guild the command message has `stopusers` defined
  in it's config, and the messsage's author's discord id is within the list found in `stopusers`
`update` - Attempt to update the bot to the newest version using this github repository.
  NOTE: This command works nearly identically the same as `stop`, but uses the `updateusers`
  config value instead.

## Automatic messaging
When StatusBot is connected to a guild and has it's `address` (and preferably also it's `channel`)
value set, StatusBot will go to the channel defined by the `channel` option (if unset, goes to first
any channels with `bot` in the title, then `general`, and if that fails then a random text channel)
and post the following message: `Server pinger started.` As long as the pinger is running every 60
secconds (on default) StatusBot will connect to and ping the server found at `address` and see if
any players have joined or left since the last time it pinged said server. If any players have
joined or left the server, StatusBot will tell you!
