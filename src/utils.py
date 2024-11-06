import logging
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

def create_logger(name: str) -> logging.Logger:
    """Creates and configures a logger with the specified name."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def create_selenium_driver(headless: bool = True) -> webdriver.Chrome:
    """Sets up and returns a Selenium WebDriver instance with specified options."""
    options = Options()
    if headless:
        options.add_argument('--headless=new')  # Updated syntax for headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-notifications')
    
    # Initialize the driver with ChromeDriverManager to handle setup
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def wait_for_element(driver: webdriver.Chrome, locator: tuple, timeout: int = 10):
    """Waits for an element to be present on the page within a timeout period."""
    logger = create_logger("wait_for_element")
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))
    except TimeoutException:
        logger.error(f"Timeout waiting for element: {locator}")
        return None

def extract_text_from_element(element) -> str:
    """Extracts and returns text content from a Selenium WebElement."""
    return element.get_attribute('textContent').strip() if element else ""
