#!/bin/bash
# -*- coding: utf-8 -*-
# Install new version of bot

cd ~/Desktop/Bots
echo "Attempting to remove old."
if [ -d "~/Desktop/Bots/old" ] ; then
    rm old
fi
echo "Moving current to old."
mv StatusBot old
echo "Installing updated bot..."
git clone https://github.com/CoolCat467/StatusBot
echo "Moving old credentials over..."
mv old/.env StatusBot/.env
echo "Moving old config over..."
mv old/src/StatusBot/config StatusBot/src/StatusBot/config

cd StatusBot/scripts
chmod 755 looprun.sh run.sh
echo "Install complete."
. looprun.sh
