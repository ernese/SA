from abc import ABC, abstractmethod

class Saver(ABC):
    """Abstract base class for saving news articles."""
    
    @abstractmethod
    def save(self, data) -> None:
        """Save the data provided. Must be implemented by concrete classes."""
        pass
