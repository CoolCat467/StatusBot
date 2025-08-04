#!/bin/bash
# -*- coding: utf-8 -*-
# Run bot in a virtual environment

export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

python3 -m pip install --upgrade uv

cd ~/Applications
# python3.11 -m venv StatusBot
cd StatusBot
# source bin/activate
uv pip install --system -e ../StatusBot
run_statusbot
# deactivate
