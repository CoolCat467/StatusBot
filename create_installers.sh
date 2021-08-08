#!/bin/bash
# -*- coding: utf-8 -*-
# Programmed by CoolCat467

VBot='StatusBot'
VAuthor='CoolCat467'
echo -n "Install Directory: "
read VInstallDir


cat > run.sh << EOF
#!/bin/bash
# -*- coding: utf-8 -*-
# Run bot in a virtual environment

cd $VInstallDir/Bots
python3 -m venv $VBot
cd $VBot
source bin/activate
python3 -m pip install -r requirements.txt
cd bot
python3 bot.py
deactivate
EOF


cat > run-quick.sh << EOF
#!/bin/bash
# -*- coding: utf-8 -*-
# Run bot in a virtual environment without trying to reinstall requirements.

cd $VInstallDir/Bots/$VBot
source bin/activate
python3 bot.py
deactivate
EOF


cat > looprun.sh << EOF
#!/bin/bash
# -*- coding: utf-8 -*-
# Loop run.sh

$VInstallDir/Bots/$VBot/run.sh
$VInstallDir/Bots/$VBot/looprun.sh
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
cd ..
chmod 755 *
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
chmod 755 *
echo "Install complete."
. looprun.sh
EOF