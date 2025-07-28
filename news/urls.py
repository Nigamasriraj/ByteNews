# bytenews/news/urls.py
from django.urls import path
from . import views

app_name = 'news' # Namespace for URLs - This is crucial!

urlpatterns = [
    path('', views.ArticleListView.as_view(), name='article_list'),
    path('article/<slug:slug>/', views.ArticleDetailView.as_view(), name='article_detail'),
    # URL for generating summary
    path('article/<slug:slug>/generate_summary/', views.generate_summary_view, name='generate_summary'),
    # URL for submitting feedback
    path('article/<slug:slug>/feedback/', views.submit_summary_feedback, name='submit_summary_feedback'),
    # URL for user's reading history
    path('history/', views.ReadingHistoryListView.as_view(), name='reading_history'),
]

