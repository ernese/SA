from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from scraper.selenium_base import BaseSeleniumScraper
from typing import Optional, Dict, List
import time

class FacebookScraper(BaseSeleniumScraper):
    BASE_URL = 'https://www.facebook.com/search/posts?q={}'
    
    def __init__(self, df, keywords: List[str], email: str, password: str):
        super().__init__(df, keywords)
        self.email = email
        self.password = password
        self.article_set = set()

    def scrape(self):
        """Main scraping method with enhanced error handling."""
        try:
            self.logger.info("Starting Facebook scraper")
            if not self._login():
                self.logger.error("Failed to log in to Facebook")
                return

            for keyword in self.keywords:
                self._scrape_keyword(keyword)
                
        except Exception as e:
            self.logger.error(f"Error during Facebook scraping: {str(e)}")
        finally:
            self.driver.quit()

    def _login(self) -> bool:
        """Enhanced login method with better error handling."""
        try:
            self.driver.get("https://www.facebook.com/login")
            
            # Wait for and fill in email
            email_field = self.wait_for_element((By.ID, "email"))
            email_field.send_keys(self.email)
            
            # Fill in password
            password_field = self.driver.find_element(By.ID, "pass")
            password_field.send_keys(self.password)
            
            # Click login button
            login_button = self.driver.find_element(By.NAME, "login")
            login_button.click()
            
            # Wait for feed to confirm successful login
            self.wait_for_element((By.CSS_SELECTOR, 'div[role="feed"]'))
            self.logger.info("Successfully logged in to Facebook")
            return True
            
        except TimeoutException:
            self.logger.error("Timeout while trying to log in")
            return False
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False

    def _scrape_keyword(self, keyword: str):
        """Scrape posts for a specific keyword with scroll pagination."""
        search_url = self.BASE_URL.format(keyword)
        self.driver.get(search_url)
        
        try:
            feed = self.wait_for_element((By.CSS_SELECTOR, 'div[role="feed"]'))
            scroll_count = 0
            max_scrolls = 5  # Limit scrolling to prevent infinite loops
            
            while scroll_count < max_scrolls:
                posts = self._extract_visible_posts()
                if not posts:
                    break
                    
                for post in posts:
                    if post['url'] in self.article_set:
                        continue
                    
                    self.save_article(post, 'Facebook')
                    self.article_set.add(post['url'])
                
                if not self._scroll_page():
                    break
                    
                scroll_count += 1
                time.sleep(2)  # Wait for new content to load
                
        except Exception as e:
            self.logger.error(f"Error scraping keyword {keyword}: {str(e)}")

    def _extract_visible_posts(self) -> List[Dict]:
        """Extract information from visible posts."""
        posts = []
        try:
            post_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="article"]')
            
            for element in post_elements:
                try:
                    post_data = {
                        'content': element.find_element(By.CSS_SELECTOR, 'div[data-ad-preview="message"]').text,
                        'url': element.find_element(By.CSS_SELECTOR, 'a[href*="/posts/"]').get_attribute('href'),
                        'timestamp': element.find_element(By.CSS_SELECTOR, 'a[href*="/posts/"] span').text,
                        'author': element.find_element(By.CSS_SELECTOR, 'h3').text
                    }
                    posts.append(post_data)
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error extracting posts: {str(e)}")
            
        return posts

    def _scroll_page(self) -> bool:
        """Scroll the page to load more content."""
        try:
            last_height = self.driver.execute_script("return document.documentElement.scrollHeight")
            self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.documentElement.scrollHeight")
            return new_height > last_height
        except Exception as e:
            self.logger.error(f"Error scrolling page: {str(e)}")
            return False