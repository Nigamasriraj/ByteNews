# bytenews/users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required # Decorator to restrict access to logged-in users
from django.contrib import messages # For displaying messages to the user
from .forms import UserPreferenceForm, CustomUserCreationForm # Import your forms
from .models import UserPreference # CORRECTED: Import UserPreference model from the current app's models

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() # Save the new user
            messages.success(request, f'Account created for {user.username}! You can now log in.')
            return redirect('login') # Redirect to the login page
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required # Ensures only logged-in users can access this view
def preferences(request):
    # Get the user's existing preferences, or create a new one if it doesn't exist
    # get_or_create is ideal for OneToOneField relationships
    user_preference, created = UserPreference.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # If form is submitted, bind data to the form instance
        form = UserPreferenceForm(request.POST, instance=user_preference)
        if form.is_valid():
            form.save() # Save the updated preferences
            messages.success(request, 'Your preferences have been updated!')
            return redirect('users:preferences') # Redirect back to the preferences page
    else:
        # If it's a GET request, pre-fill the form with existing preferences
        form = UserPreferenceForm(instance=user_preference)
    return render(request, 'users/preferences.html', {'form': form})
