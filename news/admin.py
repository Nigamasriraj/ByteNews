# bytenews/news/admin.py
from django.contrib import admin
from django.db.models import Count
from .models import Article, Category, ReadingHistory, SummaryFeedback

# Register your models here.
admin.site.register(Category)
admin.site.register(ReadingHistory)
admin.site.register(SummaryFeedback)

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'publication_date', 'link', 'approved_status_icon') # Changed to approved_status_icon
    list_filter = ('categories', 'publication_date', 'approved')
    search_fields = ('title', 'content', 'author', 'link')
    readonly_fields = ('publication_date', 'link')
    date_hierarchy = 'publication_date'

    # Custom Admin Actions for Approval Workflow
    actions = ['make_approved', 'make_pending']

    def make_approved(self, request, queryset):
        updated_count = queryset.update(approved=True)
        self.message_user(request, f'{updated_count} articles marked as approved.', level='success')
    make_approved.short_description = "Mark selected articles as Approved"

    def make_pending(self, request, queryset):
        updated_count = queryset.update(approved=False)
        self.message_user(request, f'{updated_count} articles marked as pending.', level='warning')
    make_pending.short_description = "Mark selected articles as Pending"

    # New method to display boolean icon for approved status
    def approved_status_icon(self, obj):
        return obj.approved # Return the boolean value directly
    approved_status_icon.boolean = True # This tells Django admin to display a checkmark/X
    approved_status_icon.short_description = "Approved" # Column header in admin


    # Override changelist_view to add article statistics
    def changelist_view(self, request, extra_context=None):
        total_articles = Article.objects.count()
        approved_articles = Article.objects.filter(approved=True).count()
        pending_articles = Article.objects.filter(approved=False).count()

        extra_context = extra_context or {}
        extra_context['total_articles'] = total_articles
        extra_context['approved_articles'] = approved_articles
        extra_context['pending_articles'] = pending_articles

        return super().changelist_view(request, extra_context=extra_context)

