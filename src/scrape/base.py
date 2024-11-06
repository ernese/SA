from abc import ABC, abstractmethod
import logging
import time
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from article.manager import NewsArticleManager
from article.article import NewsArticle

class BaseScraper(ABC):
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

    def __init__(self, article_manager: NewsArticleManager, keywords: List[str], rate_limit: float = 1.0):
        """
        Initialize scraper with enhanced features.
        
        Args:
            article_manager: Instance of NewsArticleManager to store results
            keywords: List of keywords to search
            rate_limit: Minimum time between requests in seconds
        """
        self.article_manager = article_manager
        self.keywords = keywords
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.session = self._create_session()
        self.logger = self._initialize_logger()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry mechanism."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update(self.HEADERS)
        return session

    def _initialize_logger(self) -> logging.Logger:
        """Initialize logger with enhanced formatting."""
        logger = logging.getLogger(self.__class__.__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

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
                tags=[article.keyword]  # You can add more tags here
            )
            self.logger.info(f"Saved article: {article.headline}")
        except Exception as e:
            self.logger.error(f"Error saving article: {str(e)}")

    @abstractmethod
    def scrape(self):
        """Abstract method to implement scraping logic."""
        pass
