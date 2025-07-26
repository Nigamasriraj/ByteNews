# ByteNews/news/admin.py
from django.contrib import admin
from .models import Category, Article, ReadingHistory # Import ReadingHistory

# Register your models here.
admin.site.register(Category)
admin.site.register(Article)
admin.site.register(ReadingHistory) # Register the new model