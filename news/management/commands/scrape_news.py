# bytenews/news/management/commands/scrape_news.py

from django.core.management.base import BaseCommand
from news.models import Article, Category
from news.utils import generate_summary, fetch_articles_from_rss
from django.utils import timezone
import time
import random
import logging

logger = logging.getLogger(__name__) # Get a logger for this command

class Command(BaseCommand):
    help = 'Scrapes news articles from predefined RSS feeds and generates summaries.'

    def handle(self, *args, **options):
        # List of RSS feeds to scrape
        rss_feeds = [
            'http://rss.cnn.com/rss/cnn_topstories.rss',
            'http://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
            'http://feeds.bbci.co.uk/news/rss.xml',
            'http://feeds.reuters.com/reuters/topNews', # Added Reuters RSS feed
        ]

        self.stdout.write(self.style.SUCCESS('Starting news scraping...'))
        total_articles_added = 0

        for feed_url in rss_feeds:
            self.stdout.write(f'Fetching articles from: {feed_url}')
            articles_data = fetch_articles_from_rss(feed_url)

            for article_data in articles_data:
                try:
                    # Check if an article with this link already exists to avoid duplicates
                    if not Article.objects.filter(link=article_data['link']).exists():
                        # Create or get categories for the article
                        article_categories = []
                        for cat_name in article_data.get('categories', []):
                            category, created = Category.objects.get_or_create(name=cat_name.strip())
                            article_categories.append(category)

                        # Create the Article instance
                        article = Article(
                            title=article_data['title'],
                            content=article_data['content'],
                            publication_date=article_data['publication_date'],
                            author=article_data['author'],
                            link=article_data['link'],
                            # summary will be generated below
                            approved=False # New articles are initially set to pending
                        )
                        # Generate summary before saving. The generate_summary function in utils
                        # will now determine the sentence count dynamically.
                        article.summary = generate_summary(article.content, article_title=article.title)
                        
                        article.save() # Save the article first to get an ID for M2M relationship

                        # Add categories to the article after it's saved
                        article.categories.set(article_categories)

                        self.stdout.write(self.style.SUCCESS(f'Successfully added: {article.title} (Pending approval)'))
                        total_articles_added += 1
                    else:
                        self.stdout.write(self.style.NOTICE(f'Article already exists (skipped): {article_data["title"]}'))

                except Exception as e:
                    logger.error(f'Error adding article "{article_data.get("title", "Unknown")}" from {feed_url}: {e}', exc_info=True)
                    self.stdout.write(self.style.ERROR(f'Error adding article "{article_data.get("title", "Unknown")}" from {feed_url}: {e}'))
            
            # Be polite to RSS servers: wait a bit between fetching different feeds
            time.sleep(random.uniform(1, 3))

        self.stdout.write(self.style.SUCCESS(f'Scraping finished. Total new articles added: {total_articles_added}'))