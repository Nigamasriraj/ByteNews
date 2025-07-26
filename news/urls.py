# bytenews/news/urls.py

from django.urls import path
from .views import ArticleListView, ArticleDetailView # Import your views

app_name = 'news' # Define the app namespace

urlpatterns = [
    # Home page - displays a list of articles (can be filtered by category or personalized)
    path('', ArticleListView.as_view(), name='article_list'),
    # Detail page for a specific article (uses primary key)
    path('article/<int:pk>/', ArticleDetailView.as_view(), name='detail'),
    # Search results page - also handled by ArticleListView, but with a 'q' parameter
    path('search/', ArticleListView.as_view(), name='search_results'),
]
