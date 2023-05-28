#!/bin/bash
# -*- coding: utf-8 -*-
# Run bot in a virtual environment

cd ~/Desktop/Bots
python3.11 -m venv StatusBot
cd StatusBot
source bin/activate
python3.11 -m pip install -e ../StatusBot
run_statusbot
deactivate
