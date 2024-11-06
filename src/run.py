from news.news_df import NewsDataFrame
from scraper.inquirer_scraper import InquirerScraper
from scraper.manila_times_scraper import ManilaTimesScraper
from scraper.bilyonaryo_scraper import BilyonaryoScraper
from scraper.facebook_scraper import FacebookScraper
import os

# Define the keywords for consistency across all scrapers
KEYWORDS = [
    'Virtual Asset Service Provider', 'Philippine Payments Management Inc.', 'Philpass', 'Pesonet',
    'Instapay', 'PDS Dealing', 'Payment',
    'BSP', 'ATM', 'GCash'
]

# Initialize a NewsDataFrame to store the scraped news information
news_df = NewsDataFrame()

# Define email and password for FacebookScraper
facebook_email = 'your_email@example.com'
facebook_password = 'your_password'

# Create instances of each scraper
scrapers = [
    ManilaTimesScraper(news_df, KEYWORDS),
    BilyonaryoScraper(news_df, KEYWORDS),
    FacebookScraper(news_df, facebook_email, facebook_password, KEYWORDS)
]

# Iterate through each Scraper instance and execute the scrape method
for scraper in scrapers:
    try:
        scraper.scrape()
    except Exception as e:
        print(f"Error running scraper {scraper.__class__.__name__}: {e}")

# Ensure the 'data' directory exists
output_dir = './data'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Save the aggregated news information in CSV and JSON formats
output_csv_path = os.path.join(output_dir, 'scraped_articles.csv')
output_json_path = os.path.join(output_dir, 'scraped_articles.json')

# Save to CSV
news_df.df.to_csv(output_csv_path, index=False)
print(f"Articles saved to {output_csv_path}")

# Save to JSON
news_df.df.to_json(output_json_path, orient='records', lines=True)
print(f"Articles saved to {output_json_path}")
