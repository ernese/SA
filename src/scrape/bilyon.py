from bs4 import BeautifulSoup, ResultSet
import requests
from scraper import Scraper
from news.news_df import NewsDataFrame
from news.news_info import NewsInfo

class BilyonaryoScraper(Scraper):
    BASE_URL = 'https://bilyonaryo.com/'
    ARTICLE_SET = set()

    KEYWORDS = [
        'Virtual Asset Service Provider', 'Philippine Payments Management Inc.', 'Philpass', 'Pesonet',
    'Instapay', 'PDS Dealing', 'Payment',
    'BSP', 'ATM', 'GCash'
    ]

    def __init__(self, df: NewsDataFrame):
        super().__init__(df, self.KEYWORDS)
        self.logger.info("BilyonaryoScraper initialized")

    def scrape(self):
        """Scrape articles for each keyword."""
        for keyword in self.KEYWORDS:
            self._scrape_keyword(keyword)

    def _scrape_keyword(self, keyword: str):
        """Scrape articles for a single keyword."""
        search_url = f"{self.BASE_URL}?s={keyword}"
        results = self._get_search_results(search_url)

        if not results:
            self.logger.info(f"No results found for keyword: {keyword}")
            return

        self.logger.info(f"Scraping articles for keyword: {keyword}")
        
        for result in results:
            article_url = self._get_article_url(result)
            if article_url in self.ARTICLE_SET:
                continue

            article_response = self._fetch_article_page(article_url)
            if not article_response:
                self.logger.error(f"Failed to fetch article at URL: {article_url}")
                continue

            news_info = self.extract_news_info(article_response, keyword)
            if news_info:
                self.articles.append(news_info)
                self.df.add_news('Bilyonaryo', news_info)
                self.ARTICLE_SET.add(article_url)
                self.logger.info(f"Added article: {article_url}")
            else:
                self._log_extraction_error(article_url, result)

    def _get_search_results(self, search_url: str) -> ResultSet:
        """Retrieve search results for a keyword."""
        response = requests.get(search_url, headers=self.HEADERS)
        if response.status_code != 200:
            self.logger.error(f"Failed to retrieve search results from {search_url}")
            return None
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.find_all('article', class_='post')

    def _get_article_url(self, result) -> str:
        """Extract the article URL from a search result."""
        return result.find('a', href=True).get('href')

    def _fetch_article_page(self, url: str) -> requests.Response:
        """Fetch the article page and return the response."""
        try:
            response = requests.get(url, headers=self.HEADERS)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            self.logger.error(f"Error fetching article page at {url}: {e}")
            return None

    def extract_news_info(self, article_response: requests.Response, keyword: str) -> NewsInfo:
        """Extract structured data from an article page."""
        try:
            page = BeautifulSoup(article_response.text, 'html.parser')
            title = page.find('h1', class_='entry-title').get_text(strip=True)
            author = page.find('span', class_='author').get_text(strip=True)
            published_date = page.find('span', class_='date').get_text(strip=True)
            content = [p.get_text(strip=True) for p in page.find('div', class_='entry-content').find_all('p')]
            return NewsInfo(keyword, published_date, title, author, 'Bilyonaryo', content)
        except AttributeError as e:
            self.logger.error(f"Error extracting news info: {e}")
            return None

    def _log_extraction_error(self, url: str, result):
        """Log an extraction error to file and console."""
        self.logger.error(f"Error extracting article info from {url}")
        with open('./log/errors.txt', 'a') as file:
            file.write(f"[{url}] {result.text}\n")
