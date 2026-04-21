#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
# ... existing commands like collectstatic and migrate ...
python create_admin.py