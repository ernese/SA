import os
import logging
from comp.manager import NewsArticleManager
from scrape.manila_times import ManilaTimesScraper
from scrape.bilyon import BilyonaryoScraper

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for keywords and output directories
KEYWORDS = [
    'Virtual Asset Service Provider', 'Philippine Payments Management Inc.', 'Philpass', 
    'Pesonet', 'Instapay', 'PDS Dealing', 'Payment', 'BSP', 'ATM', 'GCash'
]
OUTPUT_DIR = './data'
OUTPUT_CSV_PATH = os.path.join(OUTPUT_DIR, 'scraped_articles.csv')
OUTPUT_JSON_PATH = os.path.join(OUTPUT_DIR, 'scraped_articles.json')

# Initialize a NewsDataFrame to store the scraped news information
news_df = NewsArticleManager()

def run_scrapers():
    """Run each scraper and log progress and any errors encountered."""
    try:
        # Initialize the scrapers
        scrapers = [
            ManilaTimesScraper(news_df, KEYWORDS),
            BilyonaryoScraper(news_df, KEYWORDS)
            # Uncomment if using FacebookScraper with credentials
            # FacebookScraper(news_df, facebook_email, facebook_password, KEYWORDS)
        ]
        
        for scraper in scrapers:
            logger.info(f"Starting scraper: {scraper.__class__.__name__}")
            scraper.scrape()
            logger.info(f"Completed scraper: {scraper.__class__.__name__}")
        
    except Exception as e:
        logger.error(f"An error occurred during the scraping process: {str(e)}")

def save_data():
    """Save the scraped data to both CSV and JSON formats."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    try:
        # Save to CSV
        news_df.df.to_csv(OUTPUT_CSV_PATH, index=False)
        logger.info(f"Articles saved to {OUTPUT_CSV_PATH}")

        # Save to JSON
        news_df.df.to_json(OUTPUT_JSON_PATH, orient='records', lines=True)
        logger.info(f"Articles saved to {OUTPUT_JSON_PATH}")
    
    except Exception as e:
        logger.error(f"Error saving data: {str(e)}")

if __name__ == "__main__":
    run_scrapers()
    save_data()
