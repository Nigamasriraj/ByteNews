# bytenews/news/utils.py

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from collections import defaultdict
import logging
from django.utils import timezone
import pytz # For timezone handling, pip install pytz

logger = logging.getLogger(__name__)

# Ensure NLTK data is downloaded (run these once in a Python shell if not already)
# import nltk
# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('wordnet') # Often useful for more advanced text processing


def clean_html(html_content):
    """
    Cleans HTML tags from a string, leaving only plain text.
    """
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove script and style elements
    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()
    # Get text and replace multiple newlines/spaces with single ones
    text = soup.get_text()
    # Replace multiple newlines with a single space, then strip leading/trailing whitespace
    return re.sub(r'\s+', ' ', text).strip()


def generate_summary(text, num_sentences=10, article_title=""): # Changed default to 10 sentences
    """
    Generates an extractive summary of the given text based on sentence scoring.
    Prioritizes sentences containing words from the article title.
    """
    if not text:
        return "No content to summarize."

    # Clean the text before summarization
    cleaned_text = clean_html(text)
    if not cleaned_text:
        return "No readable content to summarize."

    sentences = sent_tokenize(cleaned_text)
    if len(sentences) <= num_sentences:
        return cleaned_text # Return full text if it's already short enough

    words = word_tokenize(cleaned_text.lower())
    stop_words = set(stopwords.words('english'))
    
    # Filter out stop words and non-alphabetic tokens
    filtered_words = [word for word in words if word.isalnum() and word not in stop_words]

    # Calculate word frequencies
    word_freq = defaultdict(int)
    for word in filtered_words:
        word_freq[word] += 1

    # Score sentences
    sentence_scores = defaultdict(int)
    title_words = set(word_tokenize(article_title.lower()))
    
    for i, sentence in enumerate(sentences):
        for word in word_tokenize(sentence.lower()):
            if word in word_freq:
                sentence_scores[i] += word_freq[word]
            # Boost score if word is in the article title
            if word in title_words:
                sentence_scores[i] += 2 # Give a higher boost

        # Give a slight boost to the first few sentences as they often contain key info
        if i < 2: # Boost first 2 sentences
            sentence_scores[i] += 1

    # Sort sentences by score in descending order and select top N
    # We keep the original index to preserve order
    scored_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Select the top N sentences based on score
    # Then sort them by their original position to maintain coherence
    top_sentences_indices = sorted([index for index, score in scored_sentences[:num_sentences]])
    
    # Reconstruct the summary
    summary_sentences = [sentences[i] for i in top_sentences_indices]
    
    return " ".join(summary_sentences)


def fetch_articles_from_rss(feed_url):
    """
    Fetches and parses articles from a given RSS feed URL.
    Returns a list of dictionaries, each representing an article.
    """
    articles_data = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title if hasattr(entry, 'title') else 'No Title'
            link = entry.link if hasattr(entry, 'link') else None
            
            # Use 'content' or 'summary' for article content
            content = ""
            if hasattr(entry, 'content') and entry.content:
                # content is often a list of dictionaries
                for c in entry.content:
                    if c.type == 'text/html' or c.type == 'text/plain':
                        content = c.value
                        break
                if not content and hasattr(entry, 'summary'): # Fallback to summary if content is empty
                    content = entry.summary
            elif hasattr(entry, 'summary'):
                content = entry.summary
            
            # Clean HTML from content
            cleaned_content = clean_html(content)

            # Publication date handling
            published_date = None
            if hasattr(entry, 'published_parsed'):
                try:
                    # Create naive datetime object
                    naive_date = datetime(*entry.published_parsed[:6])
                    # Make it timezone-aware using pytz.utc
                    published_date = pytz.utc.localize(naive_date)
                except Exception as e:
                    logger.warning(f"Could not parse published_parsed for '{title}': {e}")
            elif hasattr(entry, 'updated_parsed'):
                try:
                    # Create naive datetime object
                    naive_date = datetime(*entry.updated_parsed[:6])
                    # Make it timezone-aware using pytz.utc
                    published_date = pytz.utc.localize(naive_date)
                except Exception as e:
                    logger.warning(f"Could not parse updated_parsed for '{title}': {e}")
            
            if not published_date:
                # Fallback to current time if no date found (this is already timezone-aware)
                published_date = timezone.now()
                logger.warning(f"No publication date found for '{title}', using current time.")

            author = entry.author if hasattr(entry, 'author') else 'Unknown'
            
            # Extract categories/tags
            categories = []
            if hasattr(entry, 'tags'):
                for tag in entry.tags:
                    if hasattr(tag, 'term'):
                        categories.append(tag.term)
            elif hasattr(entry, 'category'): # Some feeds use 'category' directly
                categories.append(entry.category)

            if link: # Only add if a link exists
                articles_data.append({
                    'title': title,
                    'content': cleaned_content,
                    'publication_date': published_date,
                    'author': author,
                    'link': link,
                    'categories': categories,
                })
            else:
                logger.warning(f"Skipping article '{title}' due to missing link.")

    except Exception as e:
        logger.error(f"Error fetching or parsing RSS feed {feed_url}: {e}", exc_info=True)
    return articles_data

