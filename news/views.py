# bytenews/news/views.py

from django.views.generic import ListView, DetailView
from .models import Article, Category, ReadingHistory, SummaryFeedback
from users.models import UserPreference
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from .utils import generate_summary
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils.decorators import method_decorator


class ArticleListView(ListView):
    model = Article
    template_name = 'news/home.html'
    context_object_name = 'articles'
    ordering = ['-publication_date']
    paginate_by = 6

    def get_queryset(self):
        queryset = super().get_queryset()

        # Default: Only show approved articles
        queryset = queryset.filter(approved=True)

        category_name = self.request.GET.get('category')
        if category_name:
            queryset = queryset.filter(categories__name__iexact=category_name)
            return queryset

        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(categories__name__icontains=search_query)
            ).distinct()

        if self.request.user.is_authenticated:
            try:
                user_preferences = self.request.user.userpreference.preferred_categories.all()
                if user_preferences.exists():
                    queryset = queryset.filter(categories__in=user_preferences, approved=True) # Filter recommendations by approved status
                    messages.info(self.request, "Showing articles based on your preferences.")
                else:
                    messages.info(self.request, "No preferences set. Showing all articles. Go to Preferences to customize your feed!")
            except UserPreference.DoesNotExist:
                messages.info(self.request, "No preferences found for your account. Showing all articles. Go to Preferences to customize your feed!")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all().order_by('name')
        context['current_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')

        context['recommendations'] = []
        if self.request.user.is_authenticated:
            try:
                user_preferences = self.request.user.userpreference.preferred_categories.all()
                if user_preferences.exists():
                    preferred_articles = Article.objects.filter(categories__in=user_preferences, approved=True) # Filter recommendations by approved status
                    read_article_ids = self.request.user.readinghistory_set.values_list('article_id', flat=True)
                    recommendations = \
                        preferred_articles.exclude(id__in=read_article_ids).order_by('-publication_date')[:5]
                    context['recommendations'] = recommendations
            except UserPreference.DoesNotExist:
                pass

        return context

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
def generate_summary_view(request, slug):
    article = get_object_or_404(Article, slug=slug)
    generated_summary = generate_summary(article.content, article_title=article.title)
    article.summary = generated_summary
    article.save()
    return JsonResponse({'summary': generated_summary})

@login_required
@require_POST
def submit_summary_feedback(request, slug):
    article = get_object_or_404(Article, slug=slug)
    is_helpful = request.POST.get('is_helpful')

    if is_helpful is not None:
        is_helpful_bool = (is_helpful.lower() == 'true')
        SummaryFeedback.objects.update_or_create(
            user=request.user,
            article=article,
            defaults={'is_helpful': is_helpful_bool}
        )
        messages.success(request, 'Thank you for your feedback!')
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'helpful': is_helpful_bool})
        else:
            return redirect('news:article_detail', slug=slug)
    
    messages.error(request, 'Invalid feedback provided.')
    return redirect('news:article_detail', slug=slug)

