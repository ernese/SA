from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scraper.scraper import Scraper
from news.news_info import NewsInfo

class ManilaTimesScraper(Scraper):
    BASE_URL = 'https://www.manilatimes.net/tag/{}/page/{}'
    ARTICLE_SET = set()

    KEYWORDS = [
        'Virtual Asset Service Provider', 'Philippine Payments Management Inc.', 'Philpass', 'Pesonet',
    'Instapay', 'PDS Dealing', 'Payment',
    'BSP', 'ATM', 'GCash'
    ]

    def __init__(self, df):
        super().__init__(df, self.KEYWORDS)
        self.logger.info("ManilaTimesScraper initialized")

    def scrape(self):
        """Main method to scrape articles for each keyword."""
        driver = webdriver.Chrome()
        
        for keyword in self.keywords:
            page_count = self._get_page_count(keyword)
            for page in range(1, page_count + 1):
                url = self.BASE_URL.format(keyword, page)
                driver.get(url)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'tag-widget')))
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                articles = self._get_articles(soup)

                for article in articles:
                    article_url = article.get('href')
                    if article_url in self.ARTICLE_SET:
                        continue

                    article_info = self._scrape_article(driver, article_url, keyword)
                    if article_info:
                        self.articles.append(article_info)
                        self.df.add_news('Manila Times', article_info)
                        self.ARTICLE_SET.add(article_url)
                        self.logger.info(f"Scraped article: {article_url}")

        driver.quit()

    def _get_page_count(self, keyword):
        """Determine the number of pages for each keyword."""
        page_counts = {'Philippine Stock Exchange': 9, 'PSE': 2}  # Example: Update with actual counts
        return page_counts.get(keyword, 1)

    def _get_articles(self, soup):
        """Retrieve article links from a search results page."""
        return soup.find('div', class_='tag-widget').find_all('a', href=True)

    def _scrape_article(self, driver, url, keyword):
        """Visit and extract information from an individual article."""
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'article-body-content')))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        try:
            title = soup.find('h1', class_='article-title').text.strip()
            author = soup.find('a', class_='article-author-name').text.strip() if soup.find('a', class_='article-author-name') else "Unknown Author"
            published_date = soup.find('div', class_='article-publish-time').text.strip()
            content = [p.text.strip() for p in soup.find('div', 'article-body-content').find_all('p')]

            return NewsInfo(
                keyword=keyword,
                published_date=published_date,
                title=title,
                author=author,
                section="Manila Times",
                content=content
            )
        except Exception as e:
            self.logger.error(f"Error extracting article info from {url}: {e}")
            return None
