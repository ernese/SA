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
OUTPUT_FILE = os.path.join(container_directory, 'bwdata.csv')

LOG_DIR = r'C:/Users/ernes/PCMS/log'
TARGET_URLS = [
    'https://www.bworldonline.com/banking-finance/',
    'https://www.bworldonline.com/economy/',
    'https://www.bworldonline.com/world/'
]
CHROMEDRIVER_PATH = r'C:/Users/ernes/PCMS/chromedriver-win64/chromedriver.exe'
KEYWORDS_FILE = 'keywords.json'
TIMEOUT = 40
PAGE_DELAY = 10
MAX_PAGES = 1

# Configure logging
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'bwscrape.log'),
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
            if isinstance(keywords, list):
                logging.info(f"Loaded {len(keywords)} keywords from {json_file}.")
                return keywords
            else:
                logging.error("Invalid JSON format: Keywords should be a list of strings.")
                return []
    except Exception as e:
        logging.error(f"Error loading keywords from JSON: {e}")
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
    results = []
    wait = WebDriverWait(driver, TIMEOUT)

    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.td_module_10.td_module_wrap')))
        articles = driver.find_elements(By.CSS_SELECTOR, 'div.td_module_10.td_module_wrap')
        logging.info(f"Found {len(articles)} articles on the current page.")
    except TimeoutException:
        logging.error("Timeout waiting for articles to load.")
        return results

    for article in articles:
        try:
            # Extract title and link
            title_element = article.find_element(By.CSS_SELECTOR, 'h3.entry-title.td-module-title > a')
            title = title_element.text.strip()
            link = title_element.get_attribute('href').strip()

            # Extract excerpt (optional)
            try:
                excerpt_element = article.find_element(By.CSS_SELECTOR, 'div.td-excerpt')
                excerpt = excerpt_element.text.strip()
            except NoSuchElementException:
                excerpt = "No excerpt available"

            # Combine title and excerpt for keyword matching
            content = f"{title} {excerpt}".lower()

            # Check for matching keywords
            matched_keywords = [keyword for keyword in keywords if keyword.lower() in content]
            for keyword in matched_keywords:
                results.append({
                    'keyword': keyword,
                    'title': title,
                    'link': link,
                    'excerpt': excerpt
                })
                logging.info(f"Matched Article - Keyword: {keyword}, Title: {title}, Link: {link}")
        except NoSuchElementException as e:
            logging.warning(f"Skipping article due to missing elements: {e}")
            continue
        except Exception as e:
            logging.error(f"Unexpected error processing article: {e}")
            continue

    return results

def save_results(data, output_file):
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Keyword', 'Title', 'Link', 'Excerpt'])
            for article in data:
                writer.writerow([article['keyword'], article['title'], article['link'], article['excerpt']])
        logging.info(f"Results saved to {output_file}")
    except Exception as e:
        logging.error(f"Error saving results to file: {e}")

def main():
    keywords = load_keywords(KEYWORDS_FILE)
    if not keywords:
        logging.error("No keywords loaded. Exiting.")
        return

    try:
        driver = init_driver(CHROMEDRIVER_PATH, headless=True)
    except Exception as e:
        logging.critical(f"Failed to initialize WebDriver: {e}")
        return

    all_results = []

    for base_url in TARGET_URLS:
        current_url = base_url
        pages_scraped = 0

        try:
            while current_url and pages_scraped < MAX_PAGES:
                logging.info(f"Scraping page {pages_scraped + 1}: {current_url}")
                driver.get(current_url)
                time.sleep(PAGE_DELAY)  # Allow page content to load

                page_results = scrape_page(driver, keywords)
                all_results.extend(page_results)

                # Pagination handling (e.g., get next page link)
                try:
                    next_page = driver.find_element(By.CSS_SELECTOR, 'a[rel="next"]')
                    current_url = next_page.get_attribute('href')
                except NoSuchElementException:
                    logging.info("No more pages found.")
                    break

                pages_scraped += 1

        except Exception as e:
            logging.error(f"Error scraping {base_url}: {e}")
            break

    save_results(all_results, OUTPUT_FILE)

    driver.quit()
    logging.info("Web driver closed.")
    print("Scraping completed. Results saved to:", OUTPUT_FILE)

if __name__ == "__main__":
    main()
