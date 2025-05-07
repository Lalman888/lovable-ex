import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer

from app.config import settings
# from app.tasks import send_post # Import the Celery task

logger = logging.getLogger(__name__)

async def consume_requests():
    """
    Consumes messages from the KAFKA_TOPIC_REQUEST and triggers Celery tasks.

    TODO:
        - Implement robust connection handling and retries for the consumer.
        - Handle potential errors during message deserialization (JSON).
        - Ensure graceful shutdown of the consumer.
        - Integrate the actual Celery task import and call.
        - Decide on error handling if Celery task dispatch fails.
    """
    consumer = None
    try:
        consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC_REQUEST,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="post_scheduler_group", # Define a consumer group ID
            value_deserializer=lambda m: json.loads(m.decode('utf-8')), # Deserialize JSON bytes to dict
            auto_offset_reset="earliest", # Or 'latest' depending on requirements
            enable_auto_commit=True # Or manage commits manually
        )
        await consumer.start()
        logger.info(f"Kafka consumer started for topic '{settings.KAFKA_TOPIC_REQUEST}'.")

        async for msg in consumer:
            try:
                # msg.key, msg.value, msg.topic, msg.partition, msg.offset
                logger.info(f"Received message: {msg.value} from topic {msg.topic}")

                # Extract necessary data from the message value
                post_id = msg.value.get("post_id")
                platform = msg.value.get("platform")
                content = msg.value.get("content")

                if not post_id or not platform or content is None:
                    logger.error(f"Invalid message format received: {msg.value}")
                    continue # Skip invalid messages

                # Placeholder: Replace with actual Celery task call
                logger.info(f"Simulating sending task to Celery for post_id: {post_id}")
                # send_post.delay(post_id=post_id, platform=platform, content=content)

            except json.JSONDecodeError:
                logger.exception(f"Failed to decode message: {msg.value}")
            except Exception:
                logger.exception(f"Error processing message: {msg.value}")
                # Decide if processing should stop or continue

    except Exception as e:
        logger.exception(f"Kafka consumer error: {e}")
    finally:
        if consumer:
            await consumer.stop()
            logger.info("Kafka consumer stopped.")

# To run this consumer (e.g., as a separate process or managed by the app lifecycle):
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     asyncio.run(consume_requests())
