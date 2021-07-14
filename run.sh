#!/bin/bash
# -*- coding: utf-8 -*-
# Run bot in a virtual environment

cd ~/Desktop/Bots
python3 -m venv StatusBot
cd StatusBot
source bin/activate
python3 -m pip install -r requirements.txt
cd bot
python3 bot.py
deactivate
