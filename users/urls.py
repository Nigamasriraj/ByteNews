# bytenews/users/urls.py

from django.urls import path
from . import views # Import views from the current app

app_name = 'users' # Define the app namespace

urlpatterns = [
    # URL for the preferences page
    path('preferences/', views.preferences, name='preferences'),
    # REMOVED: path('login/', views.CustomLoginView.as_view(), name='login'),
    # The 'login' URL is handled directly in the main bytenews/urls.py using Django's built-in auth views.
    # The 'register' URL is also handled in the main bytenews/urls.py.
]
