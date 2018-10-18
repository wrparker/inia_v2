#! /bin/bash
deactivate
source .virtualenv/bin/activate
python proj/manage.py runserver 0.0.0.0:8000

