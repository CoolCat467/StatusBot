#!/bin/bash
# Install new verion of bot

cd ~/Desktop
cd Bots
echo "Moving current to old."
mv StatusBot old
echo "Installing updated bot..."
git clone https://github.com/CoolCat467/StatusBot
echo "Moving old credentials over..."""
mv old/.env StatusBot/.env
cd StatusBot
chmod 755 *
echo "Install complete."
. looprun.sh
