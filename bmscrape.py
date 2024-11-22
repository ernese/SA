import json
import time
import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

SCRAPEDATA_DIR = r'C:/Users/ernes/PCMS/scrapedata'
LOG_DIR = r'C:/Users/ernes/PCMS/log'

# Constants
TARGET_URL = 'https://businessmirror.com.ph/business/'
KEYWORDS_FILE = 'keywords.json'
OUTPUT_FILE = os.path.join(SCRAPEDATA_DIR, 'bmdata.json')
CHROMEDRIVER_PATH = r'C:/Users/ernes/PCMS/chromedriver-win64/chromedriver.exe' 
TIMEOUT = 15
PAGE_DELAY = 3
MAX_PAGES = 10

# Configure logging
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'bmscrape.log'),
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def load_keywords(json_file):
    """
    Load keywords from a JSON file.

    The JSON file is expected to contain a list of keyword strings.

    Args:
        json_file (str): Path to the JSON file.

    Returns:
        list: List of keyword strings.
    """
    if not os.path.exists(json_file):
        logging.error(f"Keywords file '{json_file}' does not exist.")
        return []

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            keywords = json.load(f)
            if isinstance(keywords, list) and all(isinstance(kw, str) for kw in keywords):
                logging.info(f"Loaded {len(keywords)} keywords.")
                return keywords
            else:
                logging.error("JSON file does not contain a list of keyword strings.")
                return []
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {e}")
        return []
    except Exception as e:
        logging.error(f"Error loading JSON file: {e}")
        return []

def init_driver(chromedriver_path, headless=True):
    """
    Initialize the Selenium WebDriver.

    Args:
        chromedriver_path (str): Path to the Chromedriver executable.
        headless (bool): Whether to run the browser in headless mode.

    Returns:
        webdriver.Chrome: An instance of the Chrome WebDriver.
    """
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-dev-shm-usage')

    try:
        service = ChromeService(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logging.info("Initialized Chrome WebDriver successfully.")
        return driver
    except WebDriverException as e:
        logging.error(f"Error initializing Chrome WebDriver: {e}")
        raise

def scrape_page(driver, keywords):
    """
    Scrape the current page for articles matching the keywords.

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance.
        keywords (list): List of keyword strings.

    Returns:
        dict: Dictionary mapping each keyword to a list of matching articles.
    """
    results = {kw: [] for kw in keywords}
    wait = WebDriverWait(driver, TIMEOUT)

    try:
        # Wait until at least one article is present
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'article')))
        articles = driver.find_elements(By.CSS_SELECTOR, 'article')
        logging.info(f"Found {len(articles)} articles on the current page.")
    except TimeoutException:
        logging.error("Timeout waiting for articles to load.")
        return results

    for article in articles:
        try:
            # Extract the article title and link
            title_element = article.find_element(By.CSS_SELECTOR, 'h2.entry-title a')
            title = title_element.text.strip()
            link = title_element.get_attribute('href').strip()

            # Extract the publication date
            try:
                date_element = article.find_element(By.CSS_SELECTOR, 'li.meta-date a')
                publication_date = date_element.text.strip()
            except NoSuchElementException:
                publication_date = ""

            # (Optional) Extract article summary/excerpt
            try:
                summary_element = article.find_element(By.CSS_SELECTOR, 'div.entry-summary p')
                summary = summary_element.text.strip()
            except NoSuchElementException:
                summary = ""

            # Combine title, publication date, and summary for keyword searching
            content = f"{title} {publication_date} {summary}".lower()

            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in content:
                    if not any(d['link'] == link for d in results[keyword]):
                        results[keyword].append({
                            'title': title,
                            'link': link,
                            'publication_date': publication_date,
                            'summary': summary  # Include summary if extracted
                        })
        except NoSuchElementException as e:
            logging.warning(f"Missing elements in an article: {e}")
            continue
        except Exception as e:
            logging.error(f"Unexpected error processing an article: {e}")
            continue

    # Log the number of matches per keyword on this page
    for kw in keywords:
        logging.info(f"Keyword '{kw}': Found {len(results[kw])} matching articles on this page.")

    return results

def click_load_more(driver):
    """
    Click the "Load More" button to load additional articles.

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance.

    Returns:
        bool: True if clicked successfully, False otherwise.
    """
    try:
        # Update the selector based on the actual "Load More" button
        load_more_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Load More')]")
        if load_more_button.is_displayed() and load_more_button.is_enabled():
            driver.execute_script("arguments[0].click();", load_more_button)
            logging.info("Clicked 'Load More' button.")
            return True
        else:
            logging.info("'Load More' button is not visible or not enabled.")
            return False
    except NoSuchElementException:
        logging.info("No 'Load More' button found.")
        return False
    except Exception as e:
        logging.error(f"Error clicking 'Load More' button: {e}")
        return False

def save_results(data, output_file):
    """
    Save the scraped data to a JSON file.

    Args:
        data (dict): Scraped data.
        output_file (str): Path to the output JSON file.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"Results saved to {output_file}")
    except Exception as e:
        logging.error(f"Error saving results to {output_file}: {e}")

def main():
    """
    Main function to orchestrate the scraping process.
    """
    # Load keywords
    keywords = load_keywords(KEYWORDS_FILE)
    if not keywords:
        logging.error("No keywords to search. Exiting.")
        print("No keywords to search. Exiting.")
        return

    # Initialize driver
    try:
        driver = init_driver(CHROMEDRIVER_PATH, headless=True)
    except Exception as e:
        logging.critical(f"Failed to initialize WebDriver: {e}")
        print("Failed to initialize WebDriver. Check the log for details.")
        return

    all_results = {kw: [] for kw in keywords}
    pages_scraped = 0

    try:
        driver.get(TARGET_URL)
        logging.info(f"Navigated to {TARGET_URL}")

        while pages_scraped < MAX_PAGES:
            logging.info(f"Scraping page {pages_scraped + 1}")
            scraped_data = scrape_page(driver, keywords)

            # Merge results
            for key, articles in scraped_data.items():
                for article in articles:
                    if not any(d['link'] == article['link'] for d in all_results[key]):
                        all_results[key].append(article)

            # Attempt to click the "Load More" button
            clicked = click_load_more(driver)
            if not clicked:
                logging.info("No more pages to load. Ending scraping.")
                break

            # Wait for new articles to load
            logging.info(f"Waiting for {PAGE_DELAY} seconds for new articles to load.")
            time.sleep(PAGE_DELAY)
            pages_scraped += 1

    except Exception as e:
        logging.error(f"An unexpected error occurred during scraping: {e}")
    finally:
        # Save the results
        save_results(all_results, OUTPUT_FILE)

        # Close the driver
        driver.quit()
        logging.info("Web driver closed.")
        print("Scraping completed. Check 'bmscrape.log' for details.")

if __name__ == "__main__":
    main()
