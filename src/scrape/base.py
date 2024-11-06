from abc import ABC, abstractmethod
import logging
import time
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils import create_logger 
from comp.article import NewsArticle
from comp.manager import NewsArticleManager

class BaseScraper(ABC):
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

    def __init__(self, article_manager: NewsArticleManager, keywords: List[str], rate_limit: float = 1.0):
        self.article_manager = article_manager
        self.keywords = keywords
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.logger = create_logger(self.__class__.__name__)
        self.session = self._create_session()

    def _create_session(self):
        """Create a session with retry strategy."""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        session.headers.update(self.HEADERS)
        return session

    def _rate_limit_request(self):
        """Implement rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()

    def make_request(self, url: str) -> Optional[requests.Response]:
        """Make a rate-limited request with error handling."""
        self._rate_limit_request()
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def save_article(self, article: NewsArticle, source: str):
        """Save article with error handling."""
        try:
            self.article_manager.add_news(
                news_source=source,
                keyword=article.keyword,
                date=article.date,
                headline=article.headline,
                byline=article.byline,
                section=article.section,
                content=article.content,
                url=article.url,  # Added URL field
                tags=[article.keyword]
            )
            self.logger.info(f"Saved article: {article.headline}")
        except Exception as e:
            self.logger.error(f"Error saving article: {str(e)}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    @abstractmethod
    def scrape(self):
        """Abstract method to implement scraping logic."""
        pass