from typing import List, Optional, Set
from datetime import datetime
import re
from bs4 import BeautifulSoup
from comp.article import NewsArticle
from comp.manager import NewsArticleManager
from utils import create_logger

class BilyonaryoScraper:
    BASE_URL = 'https://bilyonaryo.com/'

    def __init__(self, manager: NewsArticleManager, keywords: List[str]):
        self.manager = manager
        self.keywords = keywords
        self.logger = create_logger("BilyonaryoScraper")
        self.article_set: Set[str] = set()

    def scrape(self) -> None:
        """Scrape articles for all keywords."""
        self.logger.info("Starting Bilyonaryo scraper")
        for keyword in self.keywords:
            self._scrape_keyword(keyword)
        self.logger.info(f"Completed scraping. Found {len(self.article_set)} unique articles")

    def _scrape_keyword(self, keyword: str) -> None:
        search_url = f"{self.BASE_URL}?s={keyword}"
        response = self.manager.make_request(search_url)

        if not response:
            self.logger.warning(f"No response for keyword: {keyword}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('article', class_='post')
        self.logger.info(f"Found {len(results)} results for keyword: {keyword}")

        for result in results:
            url = self._get_article_url(result)
            if url and url not in self.article_set:
                self._scrape_article(url, keyword)

    def _get_article_url(self, result: BeautifulSoup) -> Optional[str]:
        """Extract article URL with error handling."""
        try:
            link = result.find('a', href=True)
            return link['href'] if link else None
        except Exception as e:
            self.logger.error(f"Error extracting article URL: {str(e)}")
            return None

    def _scrape_article(self, url: str, keyword: str) -> None:
        article_response = self.manager.make_request(url)
        if not article_response:
            return

        news_info = self._extract_article_info(article_response.text, keyword, url)
        if news_info:
            self.manager.save_article(news_info, 'Bilyonaryo')
            self.article_set.add(url)

    def _extract_article_info(self, html: str, keyword: str, url: str) -> Optional[NewsArticle]:
        soup = BeautifulSoup(html, 'html.parser')
        title = self.manager.safe_extract(soup, 'h1', 'entry-title')
        author = self.manager.safe_extract(soup, 'span', 'author')
        date_str = self.manager.safe_extract(soup, 'span', 'date')
        date = self._parse_date(date_str)
        content = self._extract_content(soup)

        if title and content:
            return NewsArticle(
                keyword=keyword,
                date=date,
                headline=title,
                byline=author if author != "Not found" else None,
                section='Bilyonaryo',
                content=content,
                url=url
            )
        return None

    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract and clean article content."""
        content_div = soup.find('div', class_='entry-content')
        if content_div:
            paragraphs = [
                p.text.strip() for p in content_div.find_all('p')
                if p.text.strip() and not self.manager.is_social_share_text(p.text)
            ]
            return '\n\n'.join(paragraphs) if paragraphs else None
        return None

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string into datetime object."""
        try:
            return datetime.strptime(date_str, '%B %d, %Y') if date_str else datetime.now()
        except Exception as e:
            self.logger.error(f"Error parsing date {date_str}: {str(e)}")
            return datetime.now()
