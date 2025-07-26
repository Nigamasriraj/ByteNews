# bytenews/users/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm # For user registration
from django.contrib.auth.models import User # ADDED: Import the User model
from .models import UserPreference # Correctly import UserPreference from the current app's models
from news.models import Category # Category is correctly from news.models

class CustomUserCreationForm(UserCreationForm):
    # You can add extra fields here if needed for registration, e.g., email
    class Meta(UserCreationForm.Meta):
        model = User # Explicitly set the model to User
        fields = UserCreationForm.Meta.fields + ('email',) # Example: add email field if your User model supports it

class UserPreferenceForm(forms.ModelForm):
    # ModelMultipleChoiceField with CheckboxSelectMultiple widget for checkboxes
    preferred_categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all().order_by('name'), # Get all categories, ordered by name
        widget=forms.CheckboxSelectMultiple, # This renders multiple checkboxes
        required=False # Preferences are optional
    )

    class Meta:
        model = UserPreference # Link to the UserPreference model
        fields = ['preferred_categories'] # Only this field will be displayed on the form
