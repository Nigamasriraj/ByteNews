# bytenews/users/admin.py

from django.contrib import admin
from .models import UserPreference # Correct: Only import UserPreference from users.models

# Register your models here.
admin.site.register(UserPreference) # Register UserPreference so it appears in the admin panel

# IMPORTANT: Ensure no other models (like Article, Category, ReadingHistory)
# are imported or registered in this file, as they belong in news/admin.py.
