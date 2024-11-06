from typing import List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from utils import create_selenium_driver, wait_for_element, create_logger
from base import BaseScraper
from comp.article import NewsArticle
from comp.manager import NewsArticleManager

class SeleniumBaseScraper(BaseScraper):
    def __init__(self, article_manager: NewsArticleManager, keywords: List[str], 
                 rate_limit: float = 1.0, headless: bool = True):
        super().__init__(article_manager, keywords, rate_limit)
        self.headless: bool = headless
        self.driver: Optional[WebDriver] = None

    def _initialize_driver(self) -> None:
        """Initialize the Selenium WebDriver if not already initialized."""
        if not self.driver:
            self.driver = create_selenium_driver(headless=self.headless)

    def navigate_to_page(self, url: str) -> bool:
        """
        Navigate to a page using Selenium with error handling.
        
        Args:
            url: URL to navigate to
            
        Returns:
            bool: True if navigation was successful, False otherwise
        """
        self._rate_limit_request()
        try:
            self._initialize_driver()
            self.driver.get(url)
            return True
        except WebDriverException as e:
            self.logger.error(f"Error navigating to {url}: {str(e)}")
            return False

    def wait_and_get_element(self, by: By, selector: str, timeout: int = 10) -> Optional[WebElement]:
        """
        Wait for and return an element.
        
        Args:
            by: Selenium By strategy
            selector: Element selector
            timeout: Maximum time to wait in seconds
            
        Returns:
            Optional[WebElement]: The found element or None
        """
        try:
            return wait_for_element(self.driver, (by, selector), timeout)
        except TimeoutException:
            self.logger.warning(f"Timeout waiting for element: {selector}")
            return None

    def get_page_source(self) -> Optional[str]:
        """Get the current page source with error handling."""
        try:
            return self.driver.page_source
        except WebDriverException as e:
            self.logger.error(f"Error getting page source: {str(e)}")
            return None

    def __enter__(self) -> 'SeleniumBaseScraper':
        super().__enter__()
        self._initialize_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        super().__exit__(exc_type, exc_val, exc_tb)
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.error(f"Error closing Selenium driver: {str(e)}")
            finally:
                self.driver = None