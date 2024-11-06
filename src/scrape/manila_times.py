from datetime import datetime
from typing import Optional, Set
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from scrape.selenium_base import SeleniumBaseScraper  # Updated import path
from comp.article import NewsArticle

class ManilaTimesScraper(SeleniumBaseScraper):
    """Scraper for Manila Times news articles."""
    
    BASE_URL = 'https://www.manilatimes.net/search?q={}'  # Updated to use search instead of tags
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scraped_urls: Set[str] = set()

    def scrape(self) -> None:
        """Main scraping method that processes all keywords."""
        try:
            self.logger.info("Starting Manila Times scraper")
            for keyword in self.keywords:
                self._scrape_keyword(keyword)
        except Exception as e:
            self.logger.error(f"Error during Manila Times scraping: {str(e)}")
        finally:
            self.__exit__(None, None, None)

    def _scrape_keyword(self, keyword: str) -> None:
        """Scrape all articles for a specific keyword."""
        url = self.BASE_URL.format(keyword.replace(' ', '+'))
        if not self.navigate_to_page(url):
            return

        try:
            # Wait for search results
            articles_container = self.wait_and_get_element(
                By.CLASS_NAME, 'listing-page-news', timeout=15
            )
            if not articles_container:
                self.logger.warning(f"No articles found for keyword: {keyword}")
                return

            # Get all article links
            article_links = self.driver.find_elements(
                By.CSS_SELECTOR, '.listing-page-news article a.article-title'
            )
            
            for link in article_links:
                try:
                    article_url = link.get_attribute('href')
                    if article_url and article_url not in self.scraped_urls:
                        if article := self._scrape_article(article_url, keyword):
                            self.save_article(article, "Manila Times")
                            self.scraped_urls.add(article_url)
                except Exception as e:
                    self.logger.error(f"Error processing article link: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error scraping keyword {keyword}: {str(e)}")

    def _scrape_article(self, url: str, keyword: str) -> Optional[NewsArticle]:
        """Scrape an individual article."""
        if not self.navigate_to_page(url):
            return None

        try:
            # Wait for article content
            if not self.wait_and_get_element(By.CLASS_NAME, 'article-body-content', timeout=15):
                return None

            # Extract article information
            headline = self._get_text('.article-title')
            byline = self._get_text('.article-author-name') or "Unknown Author"
            date_str = self._get_text('.article-date')
            section = self._get_text('.article-section') or "News"
            
            # Parse date
            try:
                date = datetime.strptime(date_str, '%B %d, %Y').date()
            except (ValueError, TypeError):
                self.logger.warning(f"Could not parse date: {date_str}")
                date = None

            # Get article content
            content_elements = self.driver.find_elements(
                By.CSS_SELECTOR, '.article-body-content p'
            )
            content = ' '.join(
                elem.text.strip() 
                for elem in content_elements 
                if elem.text.strip()
            )

            if not (headline and content):
                self.logger.warning(f"Missing required content for article: {url}")
                return None

            return NewsArticle(
                keyword=keyword,
                date=date,
                headline=headline,
                byline=byline,
                section=section,
                content=content,
                url=url
            )

        except Exception as e:
            self.logger.error(f"Error scraping article {url}: {str(e)}")
            return None

    def _get_text(self, selector: str) -> Optional[str]:
        """Safely extract text content from an element."""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            return element.text.strip()
        except NoSuchElementException:
            return None