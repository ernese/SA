from base import BaseScraper
from article.manager import NewsArticleManager
from article.article import NewsArticle

class BilyonaryoScraper(BaseScraper):
    BASE_URL = 'https://bilyonaryo.com/'

    def __init__(self, manager: NewsArticleManager, keywords: List[str]):
        super().__init__(manager, keywords, rate_limit=1.5)
        self.article_set = set()

    def scrape(self):
        """Scrape articles for all keywords."""
        self.logger.info("Starting Bilyonaryo scraper")
        for keyword in self.keywords:
            self._scrape_keyword(keyword)
        self.logger.info(f"Completed scraping {len(self.manager.df)} articles")

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
                    # Use the NewsArticleManager to save articles
                    self.manager.add_news(
                        news_source='Bilyonaryo',
                        keyword=news_info.keyword,
                        date=news_info.published_date,
                        headline=news_info.title,
                        byline=news_info.author,
                        section=news_info.section,
                        content=" ".join(news_info.content),
                        tags=[news_info.keyword]
                    )
                    self.article_set.add(url)
                    
            except Exception as e:
                self.logger.error(f"Error processing article {url}: {str(e)}")

    def _extract_article_info(self, html: str, keyword: str, url: str) -> Optional[NewsArticle]:
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
            
            return NewsArticle(
                keyword=keyword,
                date=date,
                headline=title,
                byline=author,
                section='Bilyonaryo',
                content=" ".join(content)
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting article info from {url}: {str(e)}")
            return None

    def _safe_extract(self, soup: BeautifulSoup, tag: str, class_name: str) -> str:
        """Safely extract text from a BeautifulSoup element."""
        element = soup.find(tag, class_=class_name)
        return element.text.strip() if element else "Not found"
