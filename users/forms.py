# bytenews/users/forms.py

from django import forms
from news.models import Category # Category is correct, it's in news.models
from .models import UserPreference # Import UserPreference from users.models
from django.contrib.auth.forms import UserCreationForm # Import Django's built-in UserCreationForm

# Assuming you have a custom User model, or you want to extend the default UserCreationForm
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        # If you have a custom user model, replace 'User' with your custom user model
        # from django.contrib.auth import get_user_model
        # User = get_user_model()
        # model = User
        fields = UserCreationForm.Meta.fields + ('email',) # Example: add email field if your user model has it

class UserPreferenceForm(forms.ModelForm):
    # We want preferred_categories to show as checkboxes, not a multi-select dropdown
    preferred_categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple,
        required=False # Preferences are optional
    )

    class Meta:
        model = UserPreference
        fields = ['preferred_categories'] # Only this field will be on the form

