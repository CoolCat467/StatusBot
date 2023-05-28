#!/bin/bash
# -*- coding: utf-8 -*-
# Install bot

cd ~/Desktop
mkdir Bots
cd Bots
echo "Installing bot..."
git clone https://github.com/CoolCat467/StatusBot

cd StatusBot
touch .env
echo "# .env" > .env
echo "DISCORD_TOKEN=" >> .env
nano .env

cd scripts
chmod 755 looprun.sh run.sh
echo "Install complete."
. looprun.sh
