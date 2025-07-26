# bytenews/news/views.py

from django.views.generic import ListView, DetailView
from .models import Article, Category, ReadingHistory # Import all necessary models
from users.models import UserPreference # Import UserPreference from the users app
from django.contrib import messages # For displaying user feedback messages
from django.db.models import Q # For complex search queries (OR conditions)

class ArticleListView(ListView):
    model = Article # The model this view will work with
    template_name = 'news/article_list.html' # The template to render
    context_object_name = 'articles' # The name of the queryset variable in the template
    ordering = ['-publication_date'] # Default ordering: newest articles first
    paginate_by = 6 # Number of articles per page for pagination

    def get_queryset(self):
        # Start with the default queryset based on the model and ordering
        queryset = super().get_queryset()

        # 1. Handle Category Filtering from URL (e.g., /?category=Sports)
        category_name = self.request.GET.get('category')
        if category_name:
            # Filter articles by category name (case-insensitive)
            queryset = queryset.filter(categories__name__iexact=category_name)
            # If a specific category is requested, we apply only that filter
            # and do not proceed with personalized or general search filters.
            return queryset

        # 2. Handle Search Query (e.g., /?q=keyword)
        search_query = self.request.GET.get('q')
        if search_query:
            # Filter articles where title, content, or category name contains the search query
            # Q objects allow for OR conditions
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(categories__name__icontains=search_query)
            ).distinct() # Use .distinct() to avoid duplicate articles if they match multiple criteria

        # 3. Handle Personalized Feed for Authenticated Users
        # This logic applies if no specific category or search query is active,
        # or if the search/category filter is applied first and then refined by preferences.
        if self.request.user.is_authenticated:
            try:
                # Access the UserPreference object via the related_name 'userpreference'
                user_preferences = self.request.user.userpreference.preferred_categories.all()
                if user_preferences.exists():
                    # If user has preferences, filter articles to include only preferred categories
                    queryset = queryset.filter(categories__in=user_preferences)
                    messages.info(self.request, "Showing articles based on your preferences.")
                else:
                    # If user is logged in but has no preferences set
                    messages.info(self.request, "No preferences set. Showing all articles. Go to Preferences to customize your feed!")
            except UserPreference.DoesNotExist:
                # If a UserPreference object doesn't exist for the logged-in user
                messages.info(self.request, "No preferences found for your account. Showing all articles. Go to Preferences to customize your feed!")
        # If user is not authenticated, the queryset remains unfiltered by preferences,
        # showing all articles (or articles filtered by category/search if present).

        return queryset

    def get_context_data(self, **kwargs):
        # Call the base implementation to get the default context
        context = super().get_context_data(**kwargs)

        # Add all categories to the context for filtering options in the template
        context['categories'] = Category.objects.all().order_by('name')
        # Pass the current category filter (if any) back to the template
        context['current_category'] = self.request.GET.get('category', '')
        # Pass the current search query (if any) back to the template
        context['search_query'] = self.request.GET.get('q', '')

        # Initialize recommendations list
        context['recommendations'] = []
        # Generate recommendations only for authenticated users
        if self.request.user.is_authenticated:
            try:
                # Get the user's preferred categories
                user_preferences = self.request.user.userpreference.preferred_categories.all()
                if user_preferences.exists():
                    # Get articles that match the preferred categories
                    preferred_articles = Article.objects.filter(categories__in=user_preferences)
                    # Get IDs of articles the user has already read
                    # Access ReadingHistory via the default related_name 'readinghistory_set'
                    read_article_ids = self.request.user.readinghistory_set.values_list('article_id', flat=True)

                    # Filter preferred articles to exclude those already read
                    # Order by publication date (newest first) and take the top 5
                    recommendations = \
                        preferred_articles.exclude(id__in=read_article_ids).order_by('-publication_date')[:5]

                    context['recommendations'] = recommendations
            except UserPreference.DoesNotExist:
                # If no preferences are set, no specific recommendations are generated
                pass
        return context

class ArticleDetailView(DetailView):
    model = Article
    template_name = 'news/article_detail.html'
    context_object_name = 'article'

    def get_object(self, queryset=None):
        # Retrieve the article object based on the URL's primary key
        obj = super().get_object(queryset)
        # Track reading history if the user is authenticated
        if self.request.user.is_authenticated:
            # Create or get a ReadingHistory entry for the current user and article
            # This prevents duplicate entries if the user views the same article multiple times
            ReadingHistory.objects.get_or_create(user=self.request.user, article=obj)
        return obj
