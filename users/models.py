# bytenews/users/models.py

from django.db import models
from django.contrib.auth.models import User # Import Django's built-in User model
from news.models import Category # Import Category from the news app

class UserPreference(models.Model):
    # OneToOneField ensures each User has at most one UserPreference object
    # related_name='userpreference' allows accessing preferences from User object: user.userpreference
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userpreference')
    # ManyToManyField for preferred categories, blank=True means it's optional
    preferred_categories = models.ManyToManyField(Category, blank=True)

    def __str__(self):
        return f"Preferences for {self.user.username}"
