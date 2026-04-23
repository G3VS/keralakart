import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keralakart.settings')
django.setup()

from django.contrib.auth.models import User

# Use simple details for now to test
username = 'admin'
password = 'TestPassword123!' 

user = User.objects.filter(username=username).first()
if user:
    user.set_password(password)
    user.save()
    print(f"✅ Password updated for '{username}'")
else:
    User.objects.create_superuser(username, 'admin@example.com', password)
    print(f"✅ Superuser '{username}' created fresh")