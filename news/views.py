from django.views.generic import ListView, DetailView
from django.shortcuts import render, redirect
from django.db.models import Q, Count
from .models import Article, Category


def home(request):
    if request.user.is_authenticated:
        return redirect('news:article_list')
    return render(request, 'home.html')


class ArticleListView(ListView):
    model = Article
    template_name = 'news/article_list.html'
    context_object_name = 'articles'
    ordering = ['-published_date']
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        category_name = self.request.GET.get('category')
        search_query = self.request.GET.get('q')

        if category_name:
            queryset = queryset.filter(category__name__iexact=category_name)

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Annotate categories with article counts
        context['categories'] = Category.objects.annotate(article_count=Count('article')).order_by('name')
        context['current_category'] = self.request.GET.get('category', 'All')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'news/article_detail.html'
    context_object_name = 'article'
