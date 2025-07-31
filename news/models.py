# bytenews/news/models.py
from django.db import models
from django.contrib.auth import get_user_model # Import to get the active User model
from django.utils.text import slugify

# Get the currently active User model
User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories" # Fix plural name in admin

    def __str__(self):
        return self.name

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    publication_date = models.DateTimeField()
    author = models.CharField(max_length=100, blank=True, null=True)
    link = models.URLField(unique=True) # Ensure article links are unique
    categories = models.ManyToManyField(Category, related_name='articles')
    summary = models.TextField(blank=True, null=True) # New field for summary
    # Ensure slug is always unique and not nullable after initial migration
    slug = models.SlugField(null=True, max_length=255, blank=True)

    # NEW FIELD FOR APPROVAL
    approved = models.BooleanField(default=False) # New field to track approval status

    class Meta:
        ordering = ['-publication_date'] # Default ordering for articles

    def save(self, *args, **kwargs):
        # Only generate slug if it's new or title has changed and slug is empty
        if not self.slug or (self._state.adding and not self.slug):
            base_slug = slugify(self.title)
            unique_slug = base_slug
            num = 1
            # Check for uniqueness, excluding the current instance if it already exists
            while Article.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    # NEW METHOD FOR ADMIN DISPLAY
    def approved_status_icon(self): # Renamed for clarity in admin
        return self.approved # Return the boolean value directly
    approved_status_icon.boolean = True # Displays a nice checkmark/x in admin
    approved_status_icon.short_description = "Approved" # Column header in admin

    def __str__(self):
        return self.title

class ReadingHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensures a user can only have one reading history entry per article
        unique_together = ('user', 'article')
        verbose_name_plural = "Reading History"

    def __str__(self):
        return f"{self.user.username} read {self.article.title[:30]}"

# New model for Summary Feedback
class SummaryFeedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    is_helpful = models.BooleanField() # True for helpful, False for not helpful
    feedback_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensures a user can only leave one feedback per article
        unique_together = ('user', 'article')
        verbose_name_plural = "Summary Feedback"

    def __str__(self):
        return f"{self.user.username} - {self.article.title[:30]} - Helpful: {self.is_helpful}"

