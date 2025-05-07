from abc import ABC, abstractmethod
from typing import Dict, Any

class PostPlatform(ABC):
    """Abstract base class for all posting platforms."""

    @abstractmethod
    async def send(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends the post content to the specific platform.

        Args:
            content: A dictionary containing platform-specific post data.

        Returns:
            A dictionary containing the result of the posting attempt
            (e.g., {'success': True, 'post_id': 'platform_post_id'} or
             {'success': False, 'error': 'error message'}).
        """
        pass
