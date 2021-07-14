#!/bin/bash
# -*- coding: utf-8 -*-
# Programmed by CoolCat467

echo -n "Install Directory: "
read VInstallDir


sudo cat > run.sh << EOF
#!/bin/bash
# -*- coding: utf-8 -*-
# Run bot in a virtual environment

cd $VInstallDir/Bots
python3 -m venv StatusBot
cd StatusBot
source bin/activate
python3 -m pip install -r requirements.txt
cd bot
python3 bot.py
deactivate
EOF


sudo cat > run-quick.sh << EOF
#!/bin/bash
# -*- coding: utf-8 -*-
# Run bot in a virtual environment without trying to reinstall requirements.

cd $VInstallDir/Bots/StatusBot
source bin/activate
python3 bot.py
deactivate
EOF


sudo cat > looprun.sh << EOF
#!/bin/bash
# -*- coding: utf-8 -*-
# Loop run.sh

$VInstallDir/Bots/StatusBot/run.sh
$VInstallDir/Bots/StatusBot/looprun.sh
EOF


sudo cat > install.sh << EOF
#!/bin/bash
# -*- coding: utf-8 -*-
# Install bot

cd $VInstallDir
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
EOF


sudo cat > install_update.sh << EOF
#!/bin/bash
# -*- coding: utf-8 -*-
# Install new verion of bot

cd $VInstallDir/Bots 
echo "Attempting to remove old."
if [ -d "$VInstallDir/Bots/old" ] ; then
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
EOF