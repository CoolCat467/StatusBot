#!/bin/bash
# Install new verion of bot

cd ~/Desktop
cd Bots
mv StatusBot old
git clone https://github.com/CoolCat467/StatusBot
mv old/.env StatusBot/.env
cd StatusBot
chmod 755 *
. looprun.sh
