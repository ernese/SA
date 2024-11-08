from typing import Optional
from save import Saver

class NewsArticle:
    """
    Represents information about a news article.
    """
    def __init__(
        self, 
        keyword: str, 
        date: str, 
        headline: str, 
        byline: str, 
        section: str, 
        content: str,
        url: Optional[str] = None
    ):
        """
        Initializes a NewsArticle object with the provided information.
        
        Parameters:
            keyword (str): The keyword associated with the news article.
            date (str): The date of the news article.
            headline (str): The headline of the news article.
            byline (str): The byline or author of the news article.
            section (str): The section or category to which the news article belongs.
            content (str): The content or body of the news article.
            url (Optional[str]): The URL of the article, if available.
        """
        self.keyword = keyword
        self.date = date
        self.headline = headline
        self.byline = byline
        self.section = section
        self.content = content
        self.url = url
        self.word_count = len(content.split())

    def save(self, saver: "Saver") -> None:
        """
        Saves the news article using the provided Saver object.
        
        Parameters:
            saver (Saver): An instance of the Saver class responsible for saving the article.
        """
        saver.save(self)

    def __str__(self) -> str:
        """Returns a string representation of the article."""
        return f"{self.headline} ({self.date}) - {self.byline}"

    def __repr__(self) -> str:
        """Returns a detailed string representation of the article."""
        return (f"NewsArticle(keyword='{self.keyword}', date='{self.date}', "
                f"headline='{self.headline}', byline='{self.byline}', "
                f"section='{self.section}', content='{self.content[:50]}...')")


