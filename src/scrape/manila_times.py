from datetime import datetime
from typing import Optional, Set
from selenium.webdriver.common.by import By
from comp.article import NewsArticle
from utils import create_selenium_driver, create_logger

class ManilaTimesScraper:
    BASE_URL = 'https://www.manilatimes.net/search?q={}'

    def __init__(self, manager, keywords):
        self.manager = manager
        self.keywords = keywords
        self.logger = create_logger("ManilaTimesScraper")
        self.driver = create_selenium_driver(headless=True)
        self.scraped_urls: Set[str] = set()

    def scrape(self) -> None:
        """Main scraping method that processes all keywords."""
        self.logger.info("Starting Manila Times scraper")
        for keyword in self.keywords:
            self._scrape_keyword(keyword)
        self.driver.quit()

    def _scrape_keyword(self, keyword: str) -> None:
        url = self.BASE_URL.format(keyword.replace(' ', '+'))
        if self.manager.navigate_to_page(self.driver, url):
            articles = self.driver.find_elements(By.CSS_SELECTOR, '.listing-page-news article a.article-title')
            for article in articles:
                article_url = article.get_attribute('href')
                if article_url and article_url not in self.scraped_urls:
                    self._scrape_article(article_url, keyword)

    def _scrape_article(self, url: str, keyword: str) -> Optional[NewsArticle]:
        if not self.manager.navigate_to_page(self.driver, url):
            return None

        headline = self.manager.safe_extract(self.driver, 'h1.article-title')
        byline = self.manager.safe_extract(self.driver, '.article-author-name') or "Unknown Author"
        date_str = self.manager.safe_extract(self.driver, '.article-date')
        section = self.manager.safe_extract(self.driver, '.article-section') or "News"
        date = self._parse_date(date_str)
        content = self._extract_content()

        if headline and content:
            article = NewsArticle(
                keyword=keyword,
                date=date,
                headline=headline,
                byline=byline,
                section=section,
                content=content,
                url=url
            )
            self.manager.save_article(article, "Manila Times")
            self.scraped_urls.add(url)

    def _extract_content(self) -> str:
        paragraphs = [
            p.text.strip() for p in self.driver.find_elements(By.CSS_SELECTOR, '.article-body-content p')
            if p.text.strip()
        ]
        return ' '.join(paragraphs)

    def _parse_date(self, date_str: str) -> datetime:
        try:
            return datetime.strptime(date_str, '%B %d, %Y').date() if date_str else None
        except (ValueError, TypeError):
            self.logger.warning(f"Could not parse date: {date_str}")
            return datetime.now()
