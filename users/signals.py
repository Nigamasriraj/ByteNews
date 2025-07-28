
from django.db.models.signals import post_save # Signal sent after a model's save() method is called
from django.contrib.auth.models import User # Django's built-in User model
from django.dispatch import receiver # Decorator to connect a function to a signal
from .models import UserPreference # CORRECTED: Ensure this import is accurate for UserPreference

# This receiver function will be called every time a User object is saved
@receiver(post_save, sender=User)
def create_or_update_user_preference(sender, instance, created, **kwargs):
    if created:
        # If a new User is created, create a corresponding UserPreference object
        UserPreference.objects.create(user=instance)