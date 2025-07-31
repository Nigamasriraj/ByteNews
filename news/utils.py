# bytenews/news/utils.py

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from collections import Counter
from bs4 import BeautifulSoup
import feedparser
import requests
from datetime import datetime
import pytz
import logging
import re
import time
import random

# --- ADDED: Import HTMLSession from requests_html ---
from requests_html import HTMLSession

logger = logging.getLogger(__name__)

# Ensure NLTK data is downloaded (run these in a Python shell if not already done)
# nltk.download('punkt')
# nltk.download('stopwords')

def clean_html(raw_html):
    """
    Removes HTML tags from a string using BeautifulSoup.
    """
    try:
        soup = BeautifulSoup(raw_html, 'html.parser')
        # Get text, preserving line breaks for better paragraph separation
        for br in soup.find_all("br"):
            br.replace_with("\n")
        return soup.get_text(separator='\n', strip=True)
    except Exception as e:
        logger.error(f"Error cleaning HTML: {e}")
        return raw_html


def fetch_articles_from_rss(rss_feed_url):
    """
    Fetches articles from a given RSS feed URL.
    Attempts to scrape the full content if available.
    Returns a list of dictionaries, each representing an article.
    """
    articles_data = []
    # --- ADDED: Create an HTMLSession instance ---
    session = HTMLSession()
    
    try:
        feed = feedparser.parse(rss_feed_url)
        for entry in feed.entries:
            title = entry.title if hasattr(entry, 'title') else 'No Title'
            link = entry.link if hasattr(entry, 'link') else None
            author = entry.author if hasattr(entry, 'author') else None
            categories = [tag.term for tag in entry.tags] if hasattr(entry, 'tags') else []

            pub_date = None
            if hasattr(entry, 'published_parsed'):
                try:
                    # Convert parsed_time tuple to datetime object
                    pub_date = datetime(*entry.published_parsed[:6])
                    # Assume UTC if no timezone info, then make it timezone-aware
                    pub_date = pytz.utc.localize(pub_date)
                except Exception as e:
                    logger.warning(f"Error parsing published_parsed date '{entry.published_parsed}': {e}")
                    pub_date = datetime.now(pytz.utc) # Fallback
            elif hasattr(entry, 'updated_parsed'):
                try:
                    pub_date = datetime(*entry.updated_parsed[:6])
                    pub_date = pytz.utc.localize(pub_date)
                except Exception as e:
                    logger.warning(f"Error parsing updated_parsed date '{entry.updated_parsed}': {e}")
                    pub_date = datetime.now(pytz.utc) # Fallback
            else:
                # Fallback to current time if no publication date is found
                pub_date = datetime.now(pytz.utc)

            full_content_scraped = ""
            if link:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                    
                    # --- MODIFIED: Use session.get instead of requests.get ---
                    response = session.get(link, headers=headers, timeout=15)
                    response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
                    
                    # --- ADDED: Render JavaScript content if needed ---
                    # Only render if the initial request.text doesn't contain the full content.
                    # This is particularly useful for sites like CNN Underscored.
                    try:
                        # Adding sleep to allow JS to load, and timeout for safety
                        # The 'scrolldown=1' can help with lazy-loaded content, but might be slow.
                        # Start without scrolldown and add if needed.
                        response.html.render(sleep=2, timeout=20) 
                    except Exception as render_e:
                        logger.warning(f"Could not render JavaScript for {link}: {render_e}. Proceeding with static HTML.")
                        # If rendering fails, we'll fall back to the initially loaded HTML.

                    # --- MODIFIED: Use response.html.html for BeautifulSoup after rendering ---
                    soup = BeautifulSoup(response.html.html, 'html.parser')

                    # Aggressive heuristic to find article content
                    article_tags = ['article', 'main', 'div', 'section']
                    possible_classes = [
                        re.compile(r'article-content|article__body|post-content|story-content|entry-content|news-body|td-post-content', re.I),
                        re.compile(r'content|body', re.I)
                    ]
                    
                    found_article_body = None
                    for tag in article_tags:
                        for cls in possible_classes:
                            found_article_body = soup.find(tag, class_=cls)
                            if found_article_body:
                                break
                        if found_article_body:
                            break
                    
                    if not found_article_body: # Fallback to general paragraph extraction if specific containers not found
                        paragraphs = soup.find_all('p')
                        full_content_scraped = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                        # Filter out very short or navigation-like paragraphs
                        full_content_scraped = '\n'.join([p for p in full_content_scraped.split('\n') if len(p.split()) > 5])
                    else:
                        full_content_scraped = found_article_body.get_text(separator='\n', strip=True)

                    # Basic cleaning of scraped content to remove excessive whitespace/line breaks
                    full_content_scraped = re.sub(r'\n\s*\n', '\n\n', full_content_scraped).strip()
                    
                    # Truncate very long scraped content to prevent memory issues or irrelevant text
                    if len(full_content_scraped) > 15000: # Limit to 15KB of text
                        full_content_scraped = full_content_scraped[:15000] + "..."

                except requests.exceptions.RequestException as e:
                    logger.error(f"HTTP/Network error fetching full content from {link}: {e}")
                except Exception as e:
                    logger.error(f"Error parsing HTML content from {link}: {e}")
            
            # If full content couldn't be scraped, fall back to RSS summary/description
            content_to_use = full_content_scraped if full_content_scraped else \
                             (entry.summary if hasattr(entry, 'summary') else \
                              (entry.description if hasattr(entry, 'description') else \
                               (entry.content[0].value if hasattr(entry, 'content') and entry.content else "")))
            
            # Ensure content is cleaned
            content_to_use = clean_html(content_to_use)

            if link and title and content_to_use and pub_date: # Ensure essential fields exist
                articles_data.append({
                    'title': title,
                    'link': link,
                    'content': content_to_use,
                    'author': author,
                    'publication_date': pub_date,
                    'categories': [tag.term for tag in entry.tags] if hasattr(entry, 'tags') else []
                })
            else:
                logger.warning(f"Skipping article due to missing essential data: Title='{title}', Link='{link}', Content_Exists={bool(content_to_use)}, Pub_Date={pub_date}")
            
            time.sleep(random.uniform(0.5, 1.5)) # Delay between 0.5 and 1.5 seconds per article

    except Exception as e:
        logger.error(f"Error fetching or parsing RSS feed {rss_feed_url}: {e}", exc_info=True)
    
    # --- ADDED: Close the session when done with the feed ---
    session.close()
    return articles_data


def generate_summary(text, article_title=""):
    """
    Generates an extractive summary of the given text.
    The number of sentences is determined dynamically based on the text length.
    Enhancements:
    - Boosts scores for words appearing in the article title.
    - Boosts scores for the first and second sentences.
    """
    if not text or not isinstance(text, str) or len(text.strip()) < 50: # Minimum text length for summarization
        return "Not enough content to generate a meaningful summary."

    text = clean_html(text)

    # 1. Tokenize into sentences
    sentences = sent_tokenize(text)

    total_sentences = len(sentences)
    min_summary_sentences = min(3, total_sentences)
    max_summary_sentences = min(10, total_sentences)

    desired_sentences = max(min_summary_sentences, min(max_summary_sentences, total_sentences // 8))
    
    if total_sentences <= desired_sentences:
        return text

    # 2. Tokenize into words and remove stop words
    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    filtered_words = [word for word in words if word.isalnum() and word not in stop_words]

    # 3. Calculate word frequencies
    word_frequencies = Counter(filtered_words)

    # Boost scores for words from the article title
    if article_title:
        title_words = word_tokenize(article_title.lower())
        for word in title_words:
            if word in word_frequencies:
                word_frequencies[word] += 0.5

    # 4. Score sentences
    sentence_scores = {}
    for i, sentence in enumerate(sentences):
        current_sentence_score = 0
        for word in word_tokenize(sentence.lower()):
            if word in word_frequencies:
                current_sentence_score += word_frequencies[word]
        
        sentence_scores[i] = current_sentence_score

        if i == 0:
            sentence_scores[i] += 2.0
        elif i == 1 and total_sentences > 1:
            sentence_scores[i] += 1.0

    # 5. Get top N sentences by score
    summarized_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)
    top_sentences_indices = [index for index, _ in summarized_sentences[:desired_sentences]]

    final_summary_sentences = [sentences[i] for i in sorted(top_sentences_indices)]

    summary = " ".join(final_summary_sentences)
    
    if not summary.strip():
        return " ".join(sentences[:min_summary_sentences]) if sentences else "Could not generate summary."

    return summary