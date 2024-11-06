from typing import List, Optional, Set
from datetime import datetime
import re
from bs4 import BeautifulSoup
from base import BaseScraper
from comp.article import NewsArticle
from comp.manager import NewsArticleManager


class BilyonaryoScraper(BaseScraper):
    BASE_URL = 'https://bilyonaryo.com/'

    def __init__(self, manager: NewsArticleManager, keywords: List[str]):
        super().__init__(manager, keywords, rate_limit=1.5)
        self.article_set: Set[str] = set()

    def scrape(self) -> None:
        """Scrape articles for all keywords."""
        self.logger.info("Starting Bilyonaryo scraper")
        try:
            for keyword in self.keywords:
                self._scrape_keyword(keyword)
            self.logger.info(f"Completed scraping. Found {len(self.article_set)} unique articles")
        except Exception as e:
            self.logger.error(f"Error in main scrape process: {str(e)}")

    def _scrape_keyword(self, keyword: str) -> None:
        """
        Scrape articles for a single keyword.
        
        Args:
            keyword: Keyword to search for
        """
        search_url = f"{self.BASE_URL}?s={keyword}"
        response = self.make_request(search_url)
        
        if not response:
            self.logger.warning(f"No response for keyword: {keyword}")
            return

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('article', class_='post')
            
            self.logger.info(f"Found {len(results)} results for keyword: {keyword}")
            
            for result in results:
                url = self._get_article_url(result)
                if not url or url in self.article_set:
                    continue
                
                article_response = self.make_request(url)
                if not article_response:
                    continue
                
                news_info = self._extract_article_info(article_response.text, keyword, url)
                if news_info:
                    self.save_article(news_info, 'Bilyonaryo')
                    self.article_set.add(url)
                
        except Exception as e:
            self.logger.error(f"Error processing keyword {keyword}: {str(e)}")

    def _get_article_url(self, result: BeautifulSoup) -> Optional[str]:
        """Extract article URL with error handling."""
        try:
            link = result.find('a', href=True)
            return link['href'] if link else None
        except Exception as e:
            self.logger.error(f"Error extracting article URL: {str(e)}")
            return None

    def _extract_article_info(self, html: str, keyword: str, url: str) -> Optional[NewsArticle]:
        """
        Extract article information with enhanced error handling.
        
        Args:
            html: Raw HTML content
            keyword: Search keyword
            url: Article URL
            
        Returns:
            Optional[NewsArticle]: Parsed article or None if extraction fails
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            title = self._safe_extract(soup, 'h1', 'entry-title')
            if not title or title == "Not found":
                return None

            author = self._safe_extract(soup, 'span', 'author')
            date_str = self._safe_extract(soup, 'span', 'date')
            date = self._parse_date(date_str)
            
            content = self._extract_content(soup)
            if not content:
                return None

            return NewsArticle(
                keyword=keyword,
                date=date,
                headline=title,
                byline=author if author != "Not found" else None,
                section='Bilyonaryo',
                content=content,
                url=url
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting article info from {url}: {str(e)}")
            return None

    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract and clean article content."""
        try:
            content_div = soup.find('div', class_='entry-content')
            if not content_div:
                return None
                
            paragraphs = []
            for p in content_div.find_all('p'):
                text = p.text.strip()
                if text and not self._is_social_share_text(text):
                    paragraphs.append(text)
                    
            return '\n\n'.join(paragraphs) if paragraphs else None
            
        except Exception as e:
            self.logger.error(f"Error extracting content: {str(e)}")
            return None

    def _safe_extract(self, soup: BeautifulSoup, tag: str, class_name: str) -> str:
        """
        Safely extract text from a BeautifulSoup element.
        
        Args:
            soup: BeautifulSoup object
            tag: HTML tag to find
            class_name: Class name to search for
            
        Returns:
            str: Extracted text or "Not found"
        """
        try:
            element = soup.find(tag, class_=class_name)
            return element.text.strip() if element else "Not found"
        except Exception as e:
            self.logger.error(f"Error extracting {tag}.{class_name}: {str(e)}")
            return "Not found"

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string into datetime object."""
        try:
            # Add your date parsing logic here based on the site's date format
            # This is a placeholder - adjust the parsing based on actual format
            if date_str == "Not found":
                return datetime.now()
            # Example parsing - modify based on actual date format
            return datetime.strptime(date_str, '%B %d, %Y')
        except Exception as e:
            self.logger.error(f"Error parsing date {date_str}: {str(e)}")
            return datetime.now()

    def _is_social_share_text(self, text: str) -> bool:
        """Check if text is social media sharing boilerplate."""
        social_patterns = [
            r'share\s+this:',
            r'like\s+this:',
            r'follow\s+us',
            r'share\s+on\s+facebook',
            r'tweet',
            r'pin\s+it'
        ]
        return any(re.search(pattern, text.lower()) for pattern in social_patterns)