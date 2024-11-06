import os
import logging
from comp.manager import NewsArticleManager
from scrape.manila_times import ManilaTimesScraper
from scrape.bilyon import BilyonaryoScraper
#from scrape.facebook import FacebookScraper

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the keywords for consistency across all scrapers
KEYWORDS = [
    'Virtual Asset Service Provider', 'Philippine Payments Management Inc.', 'Philpass', 'Pesonet',
    'Instapay', 'PDS Dealing', 'Payment',
    'BSP', 'ATM', 'GCash'
]

# Initialize a NewsDataFrame to store the scraped news information
news_df = NewsArticleManager()

# Define email and password for FacebookScraper (if applicable)
facebook_email = 'your_email@example.com'
facebook_password = 'your_password'

def run_scrapers():
    """Function to run all the scrapers sequentially."""
    try:
        # Initialize scrapers
        manila_scraper = ManilaTimesScraper(news_df, KEYWORDS)
        bilyonaryo_scraper = BilyonaryoScraper(news_df, KEYWORDS)
        #facebook_scraper = FacebookScraper(news_df, facebook_email, facebook_password, KEYWORDS)
        
        scrapers = [manila_scraper, bilyonaryo_scraper]
        
        # Run each scraper
        for scraper in scrapers:
            logger.info(f"Starting scraper: {scraper.__class__.__name__}")
            scraper.scrape()
            logger.info(f"Completed scraper: {scraper.__class__.__name__}")
        
    except Exception as e:
        logger.error(f"Error during scraping process: {str(e)}")

def save_data():
    """Save the aggregated data to CSV and JSON files."""
    output_dir = './data'
    
    # Ensure the 'data' directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_csv_path = os.path.join(output_dir, 'scraped_articles.csv')
    output_json_path = os.path.join(output_dir, 'scraped_articles.json')

    try:
        # Save to CSV
        news_df.df.to_csv(output_csv_path, index=False)
        logger.info(f"Articles saved to {output_csv_path}")

        # Save to JSON
        news_df.df.to_json(output_json_path, orient='records', lines=True)
        logger.info(f"Articles saved to {output_json_path}")
    except Exception as e:
        logger.error(f"Error saving data: {str(e)}")

if __name__ == "__main__":
    run_scrapers()
    save_data()
