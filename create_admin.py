# create_admin.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keralakart.settings')
django.setup()

from django.contrib.auth.models import User

# Replace these with the details you want
username = 'admin'
email = 'admin@example.com'
password = 'YourSecurePassword123'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superuser '{username}' created successfully!")
else:
    print(f"Superuser '{username}' already exists.")