import json
import time
import os
import datetime
import dateparser
import logging
import csv
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

# Set up directories based on today's date
today = datetime.datetime.now()
SCRAPEDATA_DIR = r'C:/Users/ernes/PCMS/scrapedata'
container_directory = f"{SCRAPEDATA_DIR}/{today.strftime('%Y')}/{today.strftime('%m')}/{today.strftime('%d')}"
os.makedirs(container_directory, exist_ok=True)
OUTPUT_FILE = os.path.join(container_directory, 'bmdata.csv')

LOG_DIR = r'C:/Users/ernes/PCMS/log'
TARGET_URL = 'https://businessmirror.com.ph/business/'
KEYWORDS_FILE = 'keywords.json'
CHROMEDRIVER_PATH = r'C:/Users/ernes/PCMS/chromedriver-win64/chromedriver.exe'
TIMEOUT = 15
PAGE_DELAY = 10
MAX_PAGES = 50

# Configure logging
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'bmscrape.log'),
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def load_keywords(json_file):
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
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
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
    results = {kw: [] for kw in keywords}
    wait = WebDriverWait(driver, TIMEOUT)

    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'article')))
        articles = driver.find_elements(By.CSS_SELECTOR, 'article')
        logging.info(f"Found {len(articles)} articles on the current page.")
    except TimeoutException:
        logging.error("Timeout waiting for articles to load.")
        return results

    for article in articles:
        try:
            title_element = article.find_element(By.CSS_SELECTOR, 'h2.entry-title a')
            title = title_element.text.strip()
            link = title_element.get_attribute('href').strip()

            try:
                date_element = article.find_element(By.CSS_SELECTOR, 'li.meta-date a')
                date_text = date_element.text.strip()
                publication_date = dateparser.parse(date_text, settings={'TIMEZONE': 'UTC', 'TO_TIMEZONE': 'UTC'})
                if publication_date:
                    publication_date = publication_date.strftime('%Y-%m-%d')
                else:
                    publication_date = "Unknown"
            except NoSuchElementException:
                publication_date = "Unknown"

            try:
                summary_element = article.find_element(By.CSS_SELECTOR, 'div.entry-summary p')
                summary = summary_element.text.strip()
            except NoSuchElementException:
                summary = ""

            content = f"{title} {publication_date} {summary}".lower()

            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in content:
                    if not any(d['link'] == link for d in results[keyword]):
                        results[keyword].append({
                            'title': title,
                            'link': link,
                            'publication_date': publication_date
                        })
        except NoSuchElementException:
            continue
        except Exception as e:
            logging.error(f"Unexpected error processing an article: {e}")
            continue

    for kw in keywords:
        logging.info(f"Keyword '{kw}': Found {len(results[kw])} matching articles on this page.")

    return results

def navigate_to_next_page(driver):
    try:
        logging.info("Attempting to locate pagination container.")
        # Locate the pagination container
        pagination_container = driver.find_element(By.CSS_SELECTOR, 'nav.navigation.pagination .nav-links')
        
        # Try to find the 'Next' button
        next_button = pagination_container.find_element(By.LINK_TEXT, 'Next')
        if next_button:
            logging.info("Found 'Next' button. Clicking to go to the next page.")
            next_button.click()
            WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'article'))  # Wait for articles to load
            )
            return True

        logging.info("No 'Next' button found. Checking for numeric pagination links.")
        
        # Check for numeric page links if 'Next' is unavailable
        current_page = pagination_container.find_element(By.CSS_SELECTOR, 'span.current')
        current_page_number = int(current_page.text.strip())
        logging.info(f"Current page: {current_page_number}")

        # Find numeric pagination links
        page_links = pagination_container.find_elements(By.CSS_SELECTOR, 'a.page-numbers')
        for link in page_links:
            try:
                page_number = int(link.text.strip())
                if page_number == current_page_number + 1:  # Look for the next page
                    logging.info(f"Navigating to page {page_number}.")
                    link.click()
                    WebDriverWait(driver, TIMEOUT).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'article'))  # Wait for articles to load
                    )
                    return True
            except ValueError:
                # Skip non-numeric links like "Previous" or other text
                continue

        logging.info("No next page found.")
        return False
    except NoSuchElementException:
        logging.info("Pagination elements not found.")
        return False
    except Exception as e:
        logging.error(f"Error navigating to the next page: {e}")
        return False




def save_results(data, output_file):
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Keyword', 'Title', 'Link', 'Publication Date'])
            for keyword, articles in data.items():
                for article in articles:
                    writer.writerow([keyword, article['title'], article['link'], article['publication_date']])
        logging.info(f"Results saved to {output_file}")
    except Exception as e:
        logging.error(f"Error saving results to {output_file}: {e}")

def main():
    keywords = load_keywords(KEYWORDS_FILE)
    if not keywords:
        logging.error("No keywords to search. Exiting.")
        print("No keywords to search. Exiting.")
        return

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

            for key, articles in scraped_data.items():
                for article in articles:
                    if not any(d['link'] == article['link'] for d in all_results[key]):
                        all_results[key].append(article)

            clicked = navigate_to_next_page(driver)
            if not clicked:
                logging.info("No more pages to navigate. Ending scraping.")
                break

            logging.info(f"Waiting for {PAGE_DELAY} seconds for new articles to load.")
            time.sleep(PAGE_DELAY)
            pages_scraped += 1

    except Exception as e:
        logging.error(f"An unexpected error occurred during scraping: {e}")
    finally:
        save_results(all_results, OUTPUT_FILE)
        driver.quit()
        logging.info("Web driver closed.")
        print("Scraping completed. Check 'bmscrape.log' for details.")

if __name__ == "__main__":
    main()
