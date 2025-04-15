import os
import django
from decouple import config

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "banking.settings")
django.setup()

from django.contrib.auth.models import User

def initialize_database():
    User.objects.create_user(
        username=config('DEFAULT_USER'),
        email=config('DEFAULT_EMAIL'),
        password=config('DEFAULT_PASSWORD')
    )

    User.objects.create_superuser(
        username=config('ADMIN_USER'),
        email=config('ADMIN_EMAIL'),
        password=config('ADMIN_PASSWORD')
    )

if __name__ == "__main__":
    initialize_database()
