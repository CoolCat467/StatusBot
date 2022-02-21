#!/bin/bash
# This will be run at startup by
# /home/pi/.config/lxsession/LXDE-pi/autostart
# @lxterminal --command="/home/pi/startup.sh"
#source /home/pi/.profile
#sleep 5
echo "starting..." >> /home/pi/startup_log.txt
#tmux new-session \; send-key "/home/pi/Desktop/Bots/StatusBot/looprun.sh" C-m \;
#tmux new "/home/pi/Desktop/Bots/StatusBot/looprun.sh"
#tmux new-session ". /home/pi/Desktop/Bots/StatusBot/looprun.sh"
#/home/pi/Desktop/Bots/StatusBot/looprun.sh

#tmux-slay run -c /home/pi/Desktop/Bots/StatusBot/looprun.sh
tmux new-session -d -s "statusbot" -n "StatusBot runner" /home/pi/Desktop/Bots/StatusBot/looprun.sh
tmux set-option -t "statusbot" destroy-unattached off
