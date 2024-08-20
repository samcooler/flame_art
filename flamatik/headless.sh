#!/bin/sh
echo "starting flamatik service with home $HOME"
# have to init pyenv
export PYENV_ROOT="/home/pi/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
# pyenv global 3.12.5

python --version

python /home/pi/flame_art/flamatik/flamatik.py -c lightcurve.cnf -l playlist.json

echo "exiting flamatik service"
