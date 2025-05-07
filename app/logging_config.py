import logging
from typing import Optional

from cmreslogging.handlers import CMRESHandler

from app.config import settings

# Global flag to prevent multiple handler initializations if called more than once
_es_handler_initialized = False

def setup_elasticsearch_logging(logger_name: Optional[str] = None):
    """
    Sets up the CMRESHandler for logging to Elasticsearch.

    Args:
        logger_name: The name of the logger to attach the handler to.
                     If None, attaches to the root logger.

    TODO:
        - Handle potential connection errors during handler initialization.
        - Configure authentication details if Elasticsearch requires them.
        - Customize the log format and index name as needed.
        - Consider using this setup in Celery workers as well.
        - Ensure ELASTIC_URL is correctly configured in settings.
    """
    global _es_handler_initialized
    if not settings.ELASTIC_URL or _es_handler_initialized:
        if not settings.ELASTIC_URL:
            logging.warning("Elasticsearch URL not configured. Skipping ES logging setup.")
        return

    logger = logging.getLogger(logger_name) # Get root logger if name is None

    # Check if the handler is already added to this specific logger
    if any(isinstance(h, CMRESHandler) for h in logger.handlers):
        logging.debug(f"CMRESHandler already configured for logger '{logger.name}'.")
        return

    try:
        handler = CMRESHandler(
            hosts=[{'host': settings.ELASTIC_URL.host, 'port': settings.ELASTIC_URL.port}],
            # auth_type=CMRESHandler.AuthType.BASIC, # Example: Add auth if needed
            # auth_details=('user', 'password'),
            es_index_name="my_app_logs", # Customize index name
            es_additional_fields={'app_name': 'SocialScheduler'} # Add custom fields
            # Use buffer_size=1 for immediate sending (development) or higher for production
        )
        logger.addHandler(handler)
        # Optional: Set level specifically for this handler
        # handler.setLevel(logging.INFO)
        logger.info(f"CMRESHandler added to logger '{logger.name}' for Elasticsearch.")
        _es_handler_initialized = True # Mark as initialized globally

    except Exception as e:
        logging.exception(f"Failed to initialize Elasticsearch logging handler: {e}")

# Example usage (e.g., in main.py or worker setup):
# if __name__ == "__main__":
#      logging.basicConfig(level=logging.INFO)
#      setup_elasticsearch_logging() # Attach to root logger
#      root_logger = logging.getLogger()
#      root_logger.warning("This is a test warning log to ES.")
#
#      app_logger = logging.getLogger("my_app_module")
#      setup_elasticsearch_logging("my_app_module") # Attach to specific logger
#      app_logger.error("This is a test error log to ES from app module.")
