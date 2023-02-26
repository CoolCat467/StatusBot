#!/bin/bash
# -*- coding: utf-8 -*-
# Programmed by CoolCat467

VBot='StatusBot'
VAuthor='CoolCat467'
VPython='python3.11'
echo -n "Install Directory: "
read VInstallDir


cat > run.sh << EOF
#!/bin/bash
# -*- coding: utf-8 -*-
# Run bot in a virtual environment

cd $VInstallDir/Bots
$VPython -m venv $VBot
cd $VBot
source bin/activate
$VPython -m pip install -r requirements.txt
$VPython bot/bot.py
deactivate
EOF


cat > run-quick.sh << EOF
#!/bin/bash
# -*- coding: utf-8 -*-
# Run bot in a virtual environment without trying to reinstall requirements.

cd $VInstallDir/Bots/$VBot
source bin/activate
$VPython bot.py
deactivate
EOF


cat > looprun.sh << EOF
#!/bin/bash
# -*- coding: utf-8 -*-
# Loop run.sh

while true do
    $VInstallDir/Bots/$VBot/run.sh
done
EOF


cat > install.sh << EOF
#!/bin/bash
# -*- coding: utf-8 -*-
# Install bot

cd $VInstallDir
mkdir Bots
cd Bots
echo "Installing bot..."
git clone https://github.com/$VAuthor/$VBot

cd $VBot/bot
touch .env
echo "# .env" > .env
echo "DISCORD_TOKEN=" >> .env
nano .env

cd $VBot
chmod 755 looprun.sh run.sh
echo "Install complete."
. looprun.sh
EOF


cat > install_update.sh << EOF
#!/bin/bash
# -*- coding: utf-8 -*-
# Install new verion of bot

cd $VInstallDir/Bots 
echo "Attempting to remove old."
if [ -d "$VInstallDir/Bots/old" ] ; then
    rm old
fi
echo "Moving current to old."
mv $VBot old
echo "Installing updated bot..."
git clone https://github.com/$VAuthor/$VBot
echo "Moving old credentials over..."
mv old/bot/.env $VBot/bot/.env
echo "Moving old config over..."
mv old/bot/config $VBot/bot/config

cd $VBot
chmod 755 looprun.sh run.sh
echo "Install complete."
. looprun.sh
EOF