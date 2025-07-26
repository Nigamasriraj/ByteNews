# bytenews/news/models.py

from django.db import models
from django.contrib.auth.models import User # Import Django's built-in User model

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories" # Corrects plural name in Django Admin

    def __str__(self):
        return self.name

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    publication_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles') # Link to User model
    categories = models.ManyToManyField(Category, related_name='articles') # Many-to-many with Category
    link = models.URLField(max_length=500, unique=True, null=True, blank=True) # ADDED: Field to store article URL

    class Meta:
        ordering = ['-publication_date'] # Default ordering for articles

    def __str__(self):
        return self.title

class ReadingHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True) # Automatically set when record is created

    class Meta:
        # Ensures a user can only have one reading history entry per article
        unique_together = ('user', 'article')
        verbose_name_plural = "Reading History" # Corrects plural name in Django Admin

    def __str__(self):
        return f"{self.user.username} read {self.article.title}"
