from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scraper.scraper import Scraper

class FacebookScraper(Scraper):
    BASE_URL = 'https://www.facebook.com/search/posts?q={}'
    ARTICLE_SET = set()

    KEYWORDS = [
        'Virtual Asset Service Provider', 'Philippine Payments Management Inc.', 'Philpass', 'Pesonet',
    'Instapay', 'PDS Dealing', 'Payment',
    'BSP', 'ATM', 'GCash'
    ]

    def __init__(self, df, email, password):
        super().__init__(df, self.KEYWORDS)
        self.email = email
        self.password = password
        self.logger.info("FacebookScraper initialized")

    def scrape(self):
        """Main scrape method to retrieve posts for each keyword."""
        driver = webdriver.Chrome()
        self._login(driver)

        for keyword in self.keywords:
            search_url = self.BASE_URL.format(keyword)
            self._scrape_keyword(driver, search_url, keyword)

        driver.quit()

    def _login(self, driver):
        """Log in to Facebook."""
        driver.get("https://www.facebook.com/login")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email"))).send_keys(self.email)
        driver.find_element(By.ID, "pass").send_keys(self.password)
        driver.find_element(By.NAME, "login").click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]')))
        self.logger.info("Logged in to Facebook")

    def _scrape_keyword(self, driver, search_url, keyword):
        """Scrape posts related to a specific keyword."""
        driver.get(search_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]')))
        self.logger.info(f"Searching for posts with keyword: {keyword}")

        while True:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            posts = self._get_posts(soup)

            for post in posts:
                post_url = self._get_post_url(post)
                if post_url in self.ARTICLE_SET:
                    continue

                post_info = self._extract_post_info(post, post_url, keyword)
                if post_info:
                    self.articles.append(post_info)
                    self.df.add_news('Facebook', post_info)
                    self.ARTICLE_SET.add(post_url)
                    self.logger.info(f"Scraped post: {post_url}")

            if not self._scroll_to_load_more(driver):
                break

    def _get_posts(self, soup):
        """Retrieve post elements from the page source."""
        return soup.find_all('div', class_='story_body_container')

    def _get_post_url(self, post):
        """Extract post URL."""
        return post.find('a', href=True).get('href') if post.find('a', href=True) else None

    def _extract_post_info(self, post, url, keyword):
        """Extract post details such as content, timestamp, and author."""
        try:
            content = post.find('div', {'data-ad-comet-preview': True}).text.strip()
            timestamp = post.find('abbr').get('title', 'Unknown time')
            author = post.find('h5').text.strip() if post.find('h5') else "Unknown Author"
            return {
                'keyword': keyword,
                'timestamp': timestamp,
                'author': author,
                'content': content,
                'url': url
            }
        except Exception as e:
            self.logger.error(f"Error extracting post info from {url}: {e}")
            return None

    def _scroll_to_load_more(self, driver):
        """Scroll to load more posts if available; return False if no more posts."""
        try:
            load_more = driver.find_element(By.CSS_SELECTOR, 'div[aria-label="See more results"]')
            driver.execute_script("arguments[0].scrollIntoView();", load_more)
            WebDriverWait(driver, 5).until(EC.staleness_of(load_more))
            return True
        except Exception:
            self.logger.info("No more results to load.")
            return False
