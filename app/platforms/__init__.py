import logging
from .base import PostPlatform # Ensure base is imported if directly referenced, though not strictly needed for PLATFORM_MAP
from .twitter import TwitterPlatform
from .facebook import FacebookPlatform

logger = logging.getLogger(__name__)

# TODO: Load platform credentials/configurations from environment variables or a config file
# and pass them to the platform constructors.
# For example:
# TWITTER_API_KEY = settings.TWITTER_API_KEY
# twitter_platform = TwitterPlatform(api_key=TWITTER_API_KEY)

PLATFORM_MAP: dict[str, PostPlatform] = {
    "twitter": TwitterPlatform(),  # Using default constructor for now
    "facebook": FacebookPlatform(), # Using default constructor for now
}

logger.info(f"PLATFORM_MAP initialized with platforms: {list(PLATFORM_MAP.keys())}")

def get_platform(platform_name: str) -> PostPlatform:
    """
    Factory function to get a platform instance.

    Args:
        platform_name (str): The name of the platform.

    Returns:
        PostPlatform: An instance of the requested platform.

    Raises:
        ValueError: If the platform_name is not supported.
    """
    platform_instance = PLATFORM_MAP.get(platform_name.lower())
    if not platform_instance:
        logger.error(f"Unsupported platform requested: {platform_name}")
        raise ValueError(f"Platform '{platform_name}' is not supported. Available platforms: {list(PLATFORM_MAP.keys())}")
    return platform_instance
