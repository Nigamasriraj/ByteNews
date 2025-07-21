from django.urls import path
from . import views

app_name = 'users'
urlpatterns = [
    path('', views.public_home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    #path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
]
