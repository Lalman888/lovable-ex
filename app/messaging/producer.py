import asyncio
import json
from typing import Optional

from aiokafka import AIOKafkaProducer

from app.config import settings

_producer: Optional[AIOKafkaProducer] = None

async def get_producer() -> AIOKafkaProducer:
    """
    Initializes and returns a singleton AIOKafkaProducer instance.

    Returns:
        The AIOKafkaProducer instance.

    Raises:
        Exception: If the producer cannot be initialized or started.

    TODO:
        - Implement robust connection handling and retries.
        - Consider lifecycle management (start/stop) within the FastAPI app lifespan.
    """
    global _producer
    if _producer is None:
        try:
            _producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                # Optional: Add authentication, TLS settings if needed
                value_serializer=lambda v: json.dumps(v).encode('utf-8') # Serialize dicts to JSON bytes
            )
            # Start the producer, potentially raise exception if connection fails
            await _producer.start()
            print("Kafka producer started successfully.")
        except Exception as e:
            print(f"Error initializing Kafka producer: {e}")
            _producer = None # Reset on failure
            raise # Re-raise the exception
    return _producer

async def stop_producer():
    """Stops the Kafka producer if it exists."""
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None
        print("Kafka producer stopped.")

async def send(topic: str, value: dict):
    """
    Sends a message to the specified Kafka topic.

    Args:
        topic: The target Kafka topic.
        value: The message value (a dictionary, will be JSON serialized).

    TODO:
        - Implement error handling for send failures (e.g., Kafka unavailable).
        - Consider adding message keys for partitioning if needed.
    """
    try:
        producer = await get_producer()
        await producer.send_and_wait(topic, value)
        print(f"Message sent to topic '{topic}': {value}")
    except Exception as e:
        # Handle exceptions (e.g., Kafka not available)
        print(f"Error sending message to Kafka topic '{topic}': {e}")
        # Depending on requirements, you might want to retry or raise the error
        # raise e # Optional: re-raise to signal failure to caller

# Example Usage (can be removed or kept for testing):
# async def main():
#     await get_producer() # Initialize
#     await send(settings.KAFKA_TOPIC_REQUEST, {"post_id": "123", "action": "schedule"})
#     await stop_producer()
#
# if __name__ == "__main__":
#     asyncio.run(main())
