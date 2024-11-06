import pandas as pd
from save import Saver

class NewsArticleManager:
    """
    Manages and stores news articles in a DataFrame format.
    """

    def __init__(self):
        self.df = pd.DataFrame(columns=['keyword', 'headline', 'published_date', 'byline', 'section', 'word_count', 'content', 'tags'])
        self.source_count = {
            'INQ': 0,
            'MAT': 0
        }
        self.SOURCE_TO_PREFIX = {
            'Inquirer': 'INQ',
            'Manila Times': 'MAT'
        }

    def add_news(self, news_source: str, keyword: str, date: str, headline: str, byline: str, section: str, content: str, tags=None, subtype=None):
        """
        Adds news article to the DataFrame.

        Parameters:
            news_source (str): The source of the news article.
            keyword (str): The keyword associated with the news article.
            date (str): The date of the news article.
            headline (str): The headline of the news article.
            byline (str): The byline or author of the news article.
            section (str): The section or category to which the news article belongs.
            content (str): The content or body of the news article.
            tags (list, optional): Additional tags for categorizing articles.
            subtype (str, optional): Optional subtype for categorizing news.
        """
        try:
            prefix = self.SOURCE_TO_PREFIX[news_source]
            count = self.source_count[prefix]
            count += 1
            ctrl_num = f'{prefix}{subtype or ""}-{count:05d}'
            
            word_count = len(content.split())
            self.df.loc[ctrl_num] = [
                keyword, headline, date, byline, section, word_count, content, ', '.join(tags or [])
            ]
            self.source_count[prefix] = count
        except KeyError as e:
            print(f"Error adding news: Unrecognized source {news_source}. Error: {e}")

    def save(self, saver: "Saver") -> None:
        """
        Saves the DataFrame using the provided Saver object.
        
        Parameters:
            saver (Saver): An instance of the Saver class responsible for saving.
        """
        saver.save(self.df)

class CSVJSONSaver(Saver):
    """
    Concrete implementation of Saver to save DataFrame as CSV and JSON.
    """

    def __init__(self, path_csv='./data/news_info.csv', path_json='./data/news_info.json'):
        self.path_csv = path_csv
        self.path_json = path_json

    def save(self, data: pd.DataFrame) -> None:
        """
        Saves the DataFrame to CSV and JSON files.
        
        Parameters:
            data (pd.DataFrame): DataFrame containing the articles to be saved.
        """
        try:
            data.to_csv(self.path_csv, index=False)
            data.to_json(self.path_json, orient='records', lines=True)
        except Exception as e:
            print(f"Error saving data: {e}")
