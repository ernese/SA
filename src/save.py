from abc import ABC, abstractmethod

class Saver(ABC):
    """Abstract base class for saving news articles."""
    
    @abstractmethod
    def save(self) -> None:
        """Save the article data. Must be implemented by concrete classes."""
        pass