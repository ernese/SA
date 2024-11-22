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
TARGET_URL = 'https://www.bworldonline.com/banking-finance/'
KEYWORDS_FILE = 'keywords.json'
OUTPUT_FILE = os.path.join(SCRAPEDATA_DIR, 'bwdata.json')
CHROMEDRIVER_PATH = r'C:/Users/ernes/PCMS/chromedriver-win64/chromedriver.exe'  
TIMEOUT = 20  
PAGE_DELAY = 5  
MAX_PAGES = 10  

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
        # Wait until at least one article is present
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'article.td_module_')))
        articles = driver.find_elements(By.CSS_SELECTOR, 'article.td_module_')
        logging.info(f"Found {len(articles)} articles on the current page.")
    except TimeoutException:
        logging.error("Timeout waiting for articles to load.")
        return results

    for article in articles:
        try:
            # Extract the article title and link
            title_element = article.find_element(By.CSS_SELECTOR, 'h3.entry-title a, h2.entry-title a')
            title = title_element.text.strip()
            link = title_element.get_attribute('href').strip()

            # Extract the publication date
            try:
                # The publication date might be within a 'time' tag or a 'span' with specific class
                date_element = article.find_element(By.CSS_SELECTOR, 'time.entry-date, span.td-module-date')
                publication_date = date_element.get_attribute('datetime') or date_element.text.strip()
            except NoSuchElementException:
                publication_date = ""

            # Combine title and publication date for keyword searching
            content = f"{title} {publication_date}".lower()

            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in content:
                    if not any(d['link'] == link for d in results[keyword]):
                        results[keyword].append({
                            'title': title,
                            'link': link,
                            'publication_date': publication_date
                        })
        except NoSuchElementException as e:
            logging.warning(f"Missing elements in an article: {e}")
            continue
        except Exception as e:
            logging.error(f"Unexpected error processing an article: {e}")
            continue

    
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
        
        load_more_button = driver.find_element(By.XPATH, "//a[contains(@class, 'td-load-more') or contains(text(), 'Load More')]")
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
        print("Scraping completed. Check 'bwscrape.log' for details.")

if __name__ == "__main__":
    main()
