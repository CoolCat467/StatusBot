#!/bin/bash

cd ~/Desktop/Bots
python3 -m venv StatusBot
cd StatusBot
source bin/activate
python3 -m pip install -r requirements.txt
cd bot
python3 bot.py
deactivate