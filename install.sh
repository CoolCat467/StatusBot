#!/bin/bash
# -*- coding: utf-8 -*-
# Install bot

cd ~/Desktop
mkdir Bots
cd Bots
echo "Installing bot..."
git clone https://github.com/CoolCat467/StatusBot
cd StatusBot/bot
touch .env
echo "# .env" > .env
echo "DISCORD_TOKEN=" >> .env
nano .env
cd ..
chmod 755 *
echo "Install complete."
. looprun.sh
