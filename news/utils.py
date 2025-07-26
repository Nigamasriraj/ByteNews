# bytenews/news/utils.py

import feedparser
import requests
import time
from datetime import datetime
import pytz # ADDED: Import pytz for timezone handling
import django.utils.timezone as timezone # Keep this for other timezone utilities if needed

def fetch_bbc_news_rss():
    """
    Fetches news articles from the BBC News RSS feed.
    Parses the feed, extracts article data, and returns a list of dictionaries.
    Includes basic error handling for network requests and parsing.
    """
    BBC_RSS_FEED_URL = "https://feeds.bbci.co.uk/news/rss.xml"
    articles_data = []

    try:
        # Fetch the feed content with requests
        # Adding a User-Agent is good practice to identify your scraper
        # Adding a timeout prevents the request from hanging indefinitely
        response = requests.get(BBC_RSS_FEED_URL, headers={'User-Agent': 'ByteNewsScraper/1.0'}, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        # Parse the feed content using feedparser
        feed = feedparser.parse(response.content)

        # Loop through each entry (article) in the feed
        for entry in feed.entries:
            title = entry.title
            link = entry.link
            # Use entry.summary or entry.description for content. Check which one exists.
            # Provides a fallback if neither is available.
            content = entry.get('summary', entry.get('description', 'No content available.'))

            # Parse publication date. feedparser often provides a parsed_tuple or utc_datetime.
            # Convert to Django's timezone-aware datetime for consistency.
            published_date = None
            if hasattr(entry, 'published_parsed'):
                # feedparser's published_parsed is a time.struct_time
                # Convert it to a timezone-aware datetime object using pytz.utc
                published_date = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc) # CORRECTED: Use pytz.utc
            elif hasattr(entry, 'published_parsed_as_datetime'): # For newer feedparser versions
                published_date = entry.published_parsed_as_datetime.astimezone(pytz.utc) # CORRECTED: Use pytz.utc
            elif hasattr(entry, 'published'): # Fallback to parsing string if other methods fail
                try:
                    # This might need more robust parsing for various date formats
                    # For simplicity, we assume feedparser's internal parsing is usually sufficient
                    # If this fallback is hit, it. means feedparser didn't provide a structured date
                    # You might add more specific strptime formats here if needed.
                    pass
                except ValueError:
                    published_date = None # Could not parse if string format is unexpected

            articles_data.append({
                'title': title,
                'link': link,
                'content': content,
                'publication_date': published_date,
                'source': 'BBC News' # Adding a source field for clarity
            })

        return articles_data

    except requests.exceptions.RequestException as e:
        # Handles network-related errors (e.g., connection refused, timeout)
        print(f"Error fetching RSS feed from BBC News: {e}")
        return []
    except Exception as e:
        # Catches any other unexpected errors during parsing or processing
        print(f"An error occurred during RSS parsing: {e}")
        return []
