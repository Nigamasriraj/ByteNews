# ByteNews/news/urls.py
from django.urls import path
from . import views # Make sure this import is present

app_name = 'news' # This defines the namespace for your app

urlpatterns = [
    # CORRECTED LINE: Use ArticleListView.as_view()
    path('', views.ArticleListView.as_view(), name='article_list'), #

    # This maps to the detail view for individual articles using their slug
    path('article/<slug:slug>/', views.ArticleDetailView.as_view(), name='article_detail'),

    # URL for reading history
    path('history/', views.ReadingHistoryListView.as_view(), name='reading_history'),

    # URL for submitting summary feedback
    path('article/<slug:slug>/feedback/', views.submit_summary_feedback, name='submit_summary_feedback'),

    # URL for generating summary (likely an AJAX endpoint)
    path('article/<slug:slug>/generate_summary/', views.generate_summary, name='generate_summary'),

    # Add other paths here as needed for your application
]