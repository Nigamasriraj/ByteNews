from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.views.generic import ListView
from news.models import Article, Category  # ✅ correct place

def public_home(request):
    if request.user.is_authenticated:
        return redirect('news:article_list')
    return render(request, 'users/home.html')  # Show login/signup if not logged in


# Login view
def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('news:article_list')  # <- VERY IMPORTANT
    return render(request, 'users/login.html', {'form': form})


# Register view
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('users:home')  # or 'dashboard'
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {'form': form})



# Logout
def logout_view(request):
    logout(request)
    return redirect('news:article_list')

# Article list view
class ArticleListView(ListView):
    model = Article
    template_name = 'news/article_list.html'
    context_object_name = 'articles'
    ordering = ['-publication_date']
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        category_name = self.request.GET.get('category')
        if category_name:
            queryset = queryset.filter(categories__name__iexact=category_name)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all().order_by('name')
        context['current_category'] = self.request.GET.get('category', 'All')
        return context
