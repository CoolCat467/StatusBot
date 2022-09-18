#!/bin/bash
# -*- coding: utf-8 -*-
# Install new verion of bot

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
mv old/bot/.env StatusBot/bot/.env
echo "Moving old config over..."
mv old/bot/config StatusBot/bot/config
cd StatusBot
chmod 755 *
echo "Install complete."
. looprun.sh
