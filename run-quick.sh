#!/bin/bash
# -*- coding: utf-8 -*-
# Run bot in a virtual environment without trying to reinstall requirements.

cd ~/Desktop/Bots/StatusBot
source bin/activate
python3 bot.py
deactivate
