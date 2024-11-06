from bs4 import BeautifulSoup
from typing import List, Optional
from scraper.base import BaseScraper
from news.news_info import NewsInfo
from news.news_df import NewsDataFrame

class BilyonaryoScraper(BaseScraper):
    BASE_URL = 'https://bilyonaryo.com/'
    
    def __init__(self, df: NewsDataFrame, keywords: List[str]):
        super().__init__(df, keywords, rate_limit=1.5)  # 1.5 second delay between requests
        self.article_set = set()

    def scrape(self):
        """Scrape articles for all keywords."""
        self.logger.info("Starting Bilyonaryo scraper")
        for keyword in self.keywords:
            self._scrape_keyword(keyword)
        self.logger.info(f"Completed scraping {len(self.articles)} articles")

    def _scrape_keyword(self, keyword: str):
        """Scrape articles for a single keyword."""
        search_url = f"{self.BASE_URL}?s={keyword}"
        response = self.make_request(search_url)
        
        if not response:
            self.logger.warning(f"No results found for keyword: {keyword}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('article', class_='post')
        
        self.logger.info(f"Found {len(results)} results for keyword: {keyword}")
        
        for result in results:
            try:
                url = result.find('a', href=True)['href']
                if url in self.article_set:
                    continue
                
                article_response = self.make_request(url)
                if not article_response:
                    continue
                
                news_info = self._extract_article_info(article_response.text, keyword, url)
                if news_info:
                    self.save_article(news_info, 'Bilyonaryo')
                    self.article_set.add(url)
                    
            except Exception as e:
                self.logger.error(f"Error processing article {url}: {str(e)}")

    def _extract_article_info(self, html: str, keyword: str, url: str) -> Optional[NewsInfo]:
        """Extract article information with enhanced error handling."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract article components with error handling
            title = self._safe_extract(soup, 'h1', 'entry-title')
            author = self._safe_extract(soup, 'span', 'author')
            date = self._safe_extract(soup, 'span', 'date')
            
            content_div = soup.find('div', class_='entry-content')
            if not content_div:
                return None
                
            content = [p.text.strip() for p in content_div.find_all('p') if p.text.strip()]
            
            return NewsInfo(
                keyword=keyword,
                published_date=date,
                title=title,
                author=author,
                section='Bilyonaryo',
                content=content,
                url=url
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting article info from {url}: {str(e)}")
            return None

    def _safe_extract(self, soup: BeautifulSoup, tag: str, class_name: str) -> str:
        """Safely extract text from a BeautifulSoup element."""
        element = soup.find(tag, class_=class_name)
        return element.text.strip() if element else "Not found"