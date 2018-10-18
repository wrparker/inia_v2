#!/bin/bash

if [ ! "$BASH_VERSION" ] ; then
    echo "Please do not use sh to run this script ($0), just execute it directly" 1>&2
    exit 1
fi

rm -rf ./.virtualenv
mkdir .virtualenv
touch .virtualenv/pip.conf
echo '[global]' >> .virtualenv/pip.conf
echo 'timeout = 1' >> .virtualenv/pip.conf
echo 'index-url =  https://pypi.org/simple' >> .virtualenv/pip.conf
virtualenv -p `which python3` .virtualenv --no-site-packages -v
source ./.virtualenv/bin/activate
echo "Checking pip"
which pip
echo "Installing Requirements"
pip install -r requirements.frozen --index https://pypi.org/simple
echo "Performing Migrations"
python proj/manage.py migrate
deactivate
echo "Environment Installed... make sure .env is available."
