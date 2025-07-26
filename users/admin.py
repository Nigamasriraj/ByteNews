# bytenews/users/admin.py

from django.contrib import admin
from .models import UserPreference # Only import UserPreference, as UserProfile doesn't exist

# Register your models here.
admin.site.register(UserPreference) # Register UserPreference so it appears in the admin panel
