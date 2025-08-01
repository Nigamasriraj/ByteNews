# bytenews/users/apps.py

from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # Import signals here so they are registered when the app is ready
        import users.signals # Make sure this line exists and is correct
