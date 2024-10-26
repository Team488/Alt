#!/bin/bash+
export PATH=$PATH:/home/pi/.pyenv/bin
if [[ -x $(command -v pyenv) ]]; then
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"
fi

pyenv activate xbot-3.9
python centralOrangePiProcess.py --sendframe False
