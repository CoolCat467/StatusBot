#!/bin/bash
# -*- coding: utf-8 -*-
# Run bot in a virtual environment

export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

cd ~/Applications
# python3.11 -m venv StatusBot
cd StatusBot
# source bin/activate
python3 -m pip install -e ../StatusBot
run_statusbot
# deactivate
