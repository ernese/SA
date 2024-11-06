from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from article.manager import NewsArticleManager
from article.article import NewsArticle
from abc import ABC, abstractmethod
from typing import List
from base import BaseScraper

class BaseSeleniumScraper(BaseScraper, ABC):
    """Base class for scrapers that require JavaScript rendering."""
    
    def __init__(self, article_manager: NewsArticleManager, keywords: List[str], headless: bool = True):
        # Initialize with the base scraper and pass the article manager
        super().__init__(article_manager, keywords)
        self.driver = self._initialize_driver(headless)
        
    def _initialize_driver(self, headless: bool) -> webdriver.Chrome:
        """Initialize Chrome driver with optimal settings."""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920x1080')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def wait_for_element(self, locator, timeout: int = 10):
        """Wait for element with explicit wait."""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )

    def save_article(self, article: NewsArticle, source: str):
        """Save article with error handling."""
        try:
            # Add the article to the article manager
            self.article_manager.add_news(
                news_source=source,
                keyword=article.keyword,
                date=article.date,
                headline=article.headline,
                byline=article.byline,
                section=article.section,
                content=article.content,
                tags=[article.keyword]  # You can add more tags here if needed
            )
            self.logger.info(f"Saved article: {article.headline}")
        except Exception as e:
            self.logger.error(f"Error saving article: {str(e)}")

    def __del__(self):
        """Ensure proper cleanup of resources."""
        if hasattr(self, 'driver'):
            self.driver.quit()

    @abstractmethod
    def scrape(self):
        """Abstract method to implement scraping logic."""
        pass
