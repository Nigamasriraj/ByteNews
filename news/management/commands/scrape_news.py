# bytenews/news/management/commands/scrape_news.py

from django.core.management.base import BaseCommand
from news.utils import fetch_bbc_news_rss # Import your scraping function
from news.models import Article, Category # Import models to save data
from django.contrib.auth.models import User # Import Django's User model
from django.utils import timezone # Import timezone for default publication date
import secrets # ADDED: Import secrets module for generating secure random strings

class Command(BaseCommand):
    help = 'Scrapes news articles from BBC RSS feed and saves them to the database.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting news scraping..."))

        # Fetch articles data using your utility function
        articles_data = fetch_bbc_news_rss()

        if not articles_data:
            self.stdout.write(self.style.WARNING("No articles fetched. Check for errors during scraping or if the feed is empty."))
            return

        articles_added = 0
        articles_skipped_duplicate = 0
        articles_skipped_no_author = 0
        articles_skipped_no_date = 0 # Added counter for missing dates

        # Get or create a default author for scraped articles
        try:
            scraper_user, created = User.objects.get_or_create(
                username='scraper_user',
                defaults={'email': 'scraper@bytenews.com', 'is_staff': True, 'is_superuser': True}
            )
            if created:
                # CORRECTED: Generate a random password string and set it on the user instance
                random_password = secrets.token_urlsafe(16) # Generate a random 16-character password
                scraper_user.set_password(random_password)
                scraper_user.save()
                self.stdout.write(self.style.WARNING(f"Created new scraper user: {scraper_user.username} with a random password."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Could not get or create scraper user: {e}. Cannot save articles without an author."))
            return


        for article_data in articles_data:
            # Ensure link exists for duplicate check
            article_link = article_data.get('link')
            if not article_link:
                self.stdout.write(self.style.WARNING(f"Skipping article '{article_data.get('title', 'Untitled')}' due to missing link."))
                continue

            # Basic check to avoid duplicates based on link.
            if Article.objects.filter(link=article_link).exists():
                articles_skipped_duplicate += 1
                continue # Skip to the next article if it's a duplicate

            # Ensure publication_date is present, default to now if not provided by feed
            publication_date = article_data.get('publication_date')
            if not publication_date:
                publication_date = timezone.now() # Use Django's timezone.now() as a fallback
                self.stdout.write(self.style.WARNING(f"Article '{article_data.get('title', 'Untitled')}' has no publication date. Using current time."))
                articles_skipped_no_date += 1 # Increment counter for articles with no date from feed

            try:
                # Create or get a default category (e.g., 'General')
                general_category, _ = Category.objects.get_or_create(name='General')

                # Create the article instance
                article = Article.objects.create(
                    title=article_data.get('title', 'Untitled Article'), # Provide a default title if missing
                    content=article_data.get('content', 'No content available.'), # Provide a default content if missing
                    publication_date=publication_date,
                    author=scraper_user, # Assign the scraper user as the author
                    link=article_link, # Save the link
                )
                # Add the article to the default 'General' category
                article.categories.add(general_category)
                articles_added += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error saving article '{article_data.get('title', 'Untitled')}': {e}"))


        self.stdout.write(self.style.SUCCESS(f"Finished scraping. Added {articles_added} new articles."))
        if articles_skipped_duplicate > 0:
            self.stdout.write(self.style.WARNING(f"Skipped {articles_skipped_duplicate} duplicate articles."))
        if articles_skipped_no_author > 0:
            self.stdout.write(self.style.WARNING(f"Skipped {articles_skipped_no_author} articles due to no author."))
        if articles_skipped_no_date > 0:
            self.stdout.write(self.style.WARNING(f"Used default date for {articles_skipped_no_date} articles."))
