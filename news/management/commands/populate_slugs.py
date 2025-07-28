# bytenews/news/management/commands/populate_slugs.py
from django.core.management.base import BaseCommand
from news.models import Article
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Populates slugs for existing articles that do not have one.'

    def handle(self, *args, **options):
        articles_updated = 0
        self.stdout.write(self.style.SUCCESS('Starting slug population for existing articles...'))

        # Filter for articles where slug is empty or None
        # Use Q objects to handle both empty string and None if your DB allows NULL
        articles_without_slug = Article.objects.filter(slug__isnull=True) | Article.objects.filter(slug='')

        for article in articles_without_slug:
            try:
                # Generate a new slug using the article's title
                base_slug = slugify(article.title)
                unique_slug = base_slug
                num = 1
                # Ensure uniqueness
                while Article.objects.filter(slug=unique_slug).exclude(pk=article.pk).exists():
                    unique_slug = f"{base_slug}-{num}"
                    num += 1
                article.slug = unique_slug
                article.save(update_fields=['slug']) # Only update the slug field
                articles_updated += 1
                self.stdout.write(self.style.SUCCESS(f'Updated slug for: {article.title}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error updating slug for article "{article.title}": {e}'))

        self.stdout.write(self.style.SUCCESS(f'Finished slug population. Total articles updated: {articles_updated}'))