from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone # Ensure timezone is imported

from .models import Article, Category, ReadingHistory, SummaryFeedback
from users.models import UserPreference

# import your util under a distinct name
from .utils import generate_summary as util_generate_summary


class ArticleListView(ListView):
    model = Article
    template_name = 'news/home.html'
    context_object_name = 'articles'
    ordering = ['-publication_date']
    paginate_by = 6

    def get_queryset(self):
        queryset = super().get_queryset()
        category_name = self.request.GET.get('category')
        if category_name:
            return queryset.filter(categories__name__iexact=category_name)

        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(categories__name__icontains=search_query)
            ).distinct()

        if self.request.user.is_authenticated:
            try:
                prefs = self.request.user.userpreference.preferred_categories.all()
                if prefs.exists():
                    queryset = queryset.filter(categories__in=prefs)
                    messages.info(self.request, "Showing articles based on your preferences.")
                else:
                    messages.info(
                        self.request,
                        "No preferences set. Showing all articles. Go to Preferences to customize your feed!"
                    )
            except UserPreference.DoesNotExist:
                messages.info(
                    self.request,
                    "No preferences found. Showing all articles. Go to Preferences to customize your feed!"
                )

        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.all().order_by('name')
        ctx['current_category'] = self.request.GET.get('category', '')
        ctx['search_query'] = self.request.GET.get('q', '')

        # recommendations based on reading history
        ctx['recommendations'] = []
        if self.request.user.is_authenticated:
            try:
                prefs = self.request.user.userpreference.preferred_categories.all()
                if prefs.exists():
                    read_ids = self.request.user.readinghistory_set.values_list('article_id', flat=True)
                    recs = (
                        Article.objects
                        .filter(categories__in=prefs)
                        .exclude(id__in=read_ids)
                        .order_by('-publication_date')[:5]
                    )
                    ctx['recommendations'] = recs
            except UserPreference.DoesNotExist:
                pass

        return ctx


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'news/article_detail.html'
    context_object_name = 'article'
    slug_url_kwarg = 'slug'
    query_pk_and_slug = True

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if self.request.user.is_authenticated:
            ReadingHistory.objects.get_or_create(user=self.request.user, article=obj)
        return obj


@method_decorator(login_required, name='dispatch')
class ReadingHistoryListView(ListView):
    model = ReadingHistory
    template_name = 'news/reading_history.html'
    context_object_name = 'reading_history_entries'
    paginate_by = 10

    def get_queryset(self):
        return ReadingHistory.objects.filter(user=self.request.user).order_by('-read_at')


@login_required
@require_POST
def submit_summary_feedback(request, slug):
    article = get_object_or_404(Article, slug=slug)
    is_helpful = request.POST.get('is_helpful')
    if is_helpful is not None:
        helpful_bool = (is_helpful.lower() == 'true')
        SummaryFeedback.objects.update_or_create(
            user=request.user,
            article=article,
            defaults={'is_helpful': helpful_bool}
        )
        messages.success(request, 'Thank you for your feedback!')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'helpful': helpful_bool})
    else:
        messages.error(request, 'Invalid feedback provided.')
    return redirect('news:article_detail', slug=slug)


@require_GET
def generate_summary(request, slug):
    article = get_object_or_404(Article, slug=slug)
    
    # Call your util function without a fixed number of sentences
    # The generate_summary function in news/utils.py will now determine the length dynamically
    summary = util_generate_summary(article.content, article_title=article.title)

    # Save it back to the article object
    article.summary = summary
    article.save(update_fields=['summary'])

    return JsonResponse({'summary': summary})