from abc import ABC, abstractmethod
from news.news_df import NewsDataFrame
from news.news_info import NewsInfo

class Scraper(ABC):
    """
    Abstract base class for web scrapers that extract news information.
    """

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    def __init__(self, df: NewsDataFrame, keywords):
        """
        Initialize a Scraper with a NewsDataFrame and list of keywords.
        """
        self.df = df
        self.keywords = keywords
        self.articles = []
        self.logger = self.initialize_logger()

    @abstractmethod
    def scrape(self):
        """ Abstract method to start scraping. Must be implemented by subclasses. """
        pass

    @abstractmethod
    def extract_info(self, page_source, url, keyword):
        """ Extract structured information from the source's page source. """
        pass

    @abstractmethod
    def get_posts(self, soup):
        """ Find and return post or article elements from a BeautifulSoup object. """
        pass

    def save_to_df(self, source_name, info):
        """ Save extracted information to NewsDataFrame. """
        self.df.add_news(source_name, info)
    
    def initialize_logger(self):
        """ Initialize and return a logger for the scraper. """
        import logging
        logger = logging.getLogger(self.__class__.__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
