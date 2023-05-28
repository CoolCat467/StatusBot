#!/bin/bash
# Startup script for statusbot using tmux

tmux new-session -d -s "statusbot" -n "StatusBot runner" /home/pi/Desktop/Bots/StatusBot/looprun.sh
tmux set-option -t "statusbot" destroy-unattached off
