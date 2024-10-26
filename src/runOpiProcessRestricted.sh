#!/bin/bash

# Initialize pyenv and activate the virtual environment

if [[ -x $(command -v pyenv) ]]; then
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"
fi

pyenv activate xbot-3.9
# Run the Python script with sudo and environment preserved
sudo -E /home/pi/.pyenv/versions/xbot-3.9/bin/python centralOrangePiProcess.py --sendframe False
