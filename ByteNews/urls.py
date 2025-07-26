# bytenews/urls.py

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views # Import Django's built-in auth views
from users import views as user_views # Import your custom user views (e.g., register)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('news.urls')), # Include news app URLs
    path('users/', include('users.urls')), # Include users app URLs

    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', user_views.register, name='register'), # Your custom register view
]
