#! /bin/bash
set -e

SCRIPT_DIR=$(dirname ${BASH_SOURCE[0]})

if ! [[ -x $(command -v pyenv) ]]; then
    echo "Pyenv must be installed."
    exit 1
fi

pyenv virtualenv --version

if [[ $(pyenv versions | grep 3.9.19 | wc -l) == "0" ]]; then
    pyenv install 3.9.19
fi

if [[ $(pyenv versions | grep xbot-3.9 | wc -l) == "0" ]]; then
    pyenv virtualenv 3.9.19 xbot-3.9
fi

eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

pyenv activate xbot-3.9

if ! [[ $(grep -c "export PYTHONPATH=$PYTHONPATH:$(realpath $SCRIPT_DIR)/src" $VIRTUAL_ENV/bin/activate) -ge 1 ]]; then
    cat <<EOF >> $VIRTUAL_ENV/bin/activate
export PYTHONPATH=$PYTHONPATH:$(realpath $SCRIPT_DIR)/src
EOF

pyenv deactivate xbot-3.9
pyenv activate xbot-3.9
fi

export PYTHONPATH=$PYTHONPATH:$(realpath $SCRIPT_DIR)/src

pip install -r $SCRIPT_DIR/requirements.txt
pip install -r $SCRIPT_DIR/dev-requirements.txt

pre-commit install
pyenv rehash
