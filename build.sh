#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python -c "from keralakart.storage_backends import CloudinaryStorage; print('Storage backend found OK')"
python manage.py shell < seed_data.py