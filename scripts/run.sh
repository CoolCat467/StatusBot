#!/bin/bash
# -*- coding: utf-8 -*-
# Run bot in a virtual environment

cd ~/Applications
# python3.11 -m venv StatusBot
cd StatusBot
# source bin/activate
python3 -m pip install -e ../StatusBot
run_statusbot
# deactivate
