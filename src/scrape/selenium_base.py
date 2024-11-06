from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class BaseSeleniumScraper(BaseScraper):
    """Base class for scrapers that require JavaScript rendering."""
    
    def __init__(self, df: NewsDataFrame, keywords: List[str], headless: bool = True):
        super().__init__(df, keywords)
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

    def __del__(self):
        """Ensure proper cleanup of resources."""
        if hasattr(self, 'driver'):
            self.driver.quit()

# utils/parallel.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable
import logging

logger = logging.getLogger(__name__)

def parallel_process(items: List, process_func: Callable, max_workers: int = 4):
    """
    Process items in parallel using ThreadPoolExecutor.
    
    Args:
        items: List of items to process
        process_func: Function to process each item
        max_workers: Maximum number of parallel workers
    """
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {
            executor.submit(process_func, item): item for item in items
        }
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Error processing {item}: {str(e)}")
    return results