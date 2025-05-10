from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class PostPlatform(ABC):
    """Abstract base class for a social media platform integration."""

    @abstractmethod
    def send(self, content: dict) -> dict:
        """
        Sends content to the specific social media platform.

        Args:
            content (dict): A dictionary containing the post details. 
                            Structure depends on the platform's requirements.
                            Example: {"text": "Hello world!", "image_url": "..."}

        Returns:
            dict: A dictionary containing the response from the platform, 
                  typically including post ID or status.
                  Example: {"id": "12345", "status": "posted"}
        
        Raises:
            NotImplementedError: If the platform's send method is not implemented.
            Exception: For any API call or other operational errors.
        """
        pass

    def __str__(self) -> str:
        return self.__class__.__name__
