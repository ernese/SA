from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from scraper.selenium_base import BaseSeleniumScraper
from news.news_info import NewsInfo
from typing import Optional, List
import time

class ManilaTimesScraper(BaseSeleniumScraper):
    BASE_URL = 'https://www.manilatimes.net/tag/{}/page/{}'
    
    def __init__(self, df, keywords: List[str]):
        super().__init__(df, keywords)
        self.article_set = set()

    def scrape(self):
        """Enhanced main scraping method."""
        try:
            self.logger.info("Starting Manila Times scraper")
            for keyword in self.keywords:
                page_num = 1
                while self._scrape_page(keyword, page_num):
                    page_num += 1
                    
        except Exception as e:
            self.logger.error(f"Error during Manila Times scraping: {str(e)}")
        finally:
            self.driver.quit()

    def _scrape_page(self, keyword: str, page: int) -> bool:
        """Scrape a single page of articles."""
        url = self.BASE_URL.format(keyword, page)
        self.driver.get(url)
        
        try:
            # Wait for article container
            self.wait_for_element((By.CLASS_NAME, 'tag-widget'))
            
            # Extract all article links
            article_links = self.driver.find_elements(By.CSS_SELECTOR, '.tag-widget article a')
            if not article_links:
                return False
                
            urls = [link.get_attribute('href') for link in article_links]
            
            for url in urls:
                if url in self.article_set:
                    continue
                    
                article_info = self._scrape_article(url, keyword)
                if article_info:
                    self.save_article(article_info, 'Manila Times')
                    self.article_set.add(url)
                    
            return True
            
        except TimeoutException:
            self.logger.warning(f"No more pages found for keyword {keyword}")
            return False
        except Exception as e:
            self.logger.error(f"Error scraping page {page} for keyword {keyword}: {str(e)}")
            return False

    def _scrape_article(self, url: str, keyword: str) -> Optional[NewsInfo]:
        """Scrape an individual article with enhanced error handling."""
        try:
            self.driver.get(url)
            
            # Wait for article content
            self.wait_for_element((By.CLASS_NAME, 'article-body-content'))
            
            # Extract article information
            title = self._safe_get_text('.article-title')
            author = self._safe_get_text('.article-author-name') or "Unknown Author"
            date = self._safe_get_text('.article-publish-time')
            
            # Extract content paragraphs
            content_elements = self.driver.find_elements(By.CSS_SELECTOR, '.article-body-content p')
            content = [elem.text.strip() for elem in content_elements if elem.text.strip()]
            
            return NewsInfo(
                keyword=keyword,
                published_date=date,
                title=title,
                author=author,
                section="Manila Times",
                content=content,
                url=url
            )
            
        except Exception as e:
            self.logger.error(f"Error scraping article {url}: {str(e)}")
            return None

    def _safe_get_text(self, selector: str) -> str:
        """Safely get text from an element."""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            return element.text.strip()
        except Exception:
            return ""