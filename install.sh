#!/bin/bash
# Install bot

cd ~/Desktop
mkdir Bots
cd Bots
# remove if it exists
# rm -r StatusBot
mv StatusBot old
git clone https://github.com/CoolCat467/StatusBot
mv old/.env StatusBot/.env
cd StatusBot
chmod 755 *
. looprun.sh
