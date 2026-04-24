#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input --clear
python manage.py makemigrations
python manage.py migrate
python manage.py shell < seed_data.py