#!/bin/bash
# Install bot

cd ~/Desktop
mkdir Bots
cd Bots
git clone https://github.com/CoolCat467/StatusBot
cd StatusBot/bot
touch .env
echo "# .env" > .env
echo "DISCORD_TOKEN=" >> .env
nano .env
chmod 755 *
cd ..
. looprun.sh
