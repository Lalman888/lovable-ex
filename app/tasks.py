import logging
import time
from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger

from app.config import settings
from app.crud import post as crud_post
from app.crud.post import get_db # Assuming get_db is available here or manage context
from app.platforms import get_platform
from app.messaging.producer import send as send_kafka_message # For status updates

# TODO: Configure Elasticsearch logging handler if needed for tasks
logger = get_task_logger(__name__)

# Initialize Celery
cel = Celery(
    'tasks',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks'] # Point to this module to find tasks
)

# Optional: Configure Celery directly
cel.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Allow json content
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@cel.task(bind=True, max_retries=3, default_retry_delay=60) # Exponential backoff might be better
async def send_post(self, post_id: str, platform_name: str, content: dict):
    """
    Celery task to send a post to a specified platform.

    Args:
        self: The task instance (automatically passed with bind=True).
        post_id: The ID of the post record in the database.
        platform_name: The name of the target platform (e.g., "twitter").
        content: The platform-specific content dictionary.

    TODO:
        - Refine retry logic (e.g., specific exceptions to retry on).
        - Implement proper async database operations within the task.
        - Add detailed logging to Elasticsearch via CMRESHandler.
        - Send status updates (success/failure) to Kafka status topic.
        - Handle platform-specific errors more gracefully.
    """
    logger.info(f"Task started: send_post for post_id={post_id}, platform={platform_name}")
    db = await get_db() # Get DB session/connection - manage lifecycle appropriately

    try:
        # 1. Get platform implementation
        platform = get_platform(platform_name)

        # 2. Update status to 'processing' in DB
        await crud_post.update_post_status(db, post_id, status='processing')
        logger.info(f"Updated post {post_id} status to 'processing'")

        # 3. Send the post via the platform's send method
        result = await platform.send(content)
        logger.info(f"Platform send result for post {post_id}: {result}")

        # 4. Handle result and update DB
        if result.get("success"):
            await crud_post.update_post_status(db, post_id, status='posted')
            # Optionally store platform_post_id from result if needed
            logger.info(f"Successfully posted post {post_id} to {platform_name}.")
            # Send success status to Kafka
            await send_kafka_message(
                settings.KAFKA_TOPIC_STATUS,
                {"post_id": post_id, "status": "posted", "platform_post_id": result.get("post_id")}
            )
        else:
            error_msg = result.get("error", "Unknown platform error")
            await crud_post.update_post_status(db, post_id, status='failed', error_message=error_msg)
            logger.error(f"Failed to post post {post_id} to {platform_name}: {error_msg}")
            # Send failure status to Kafka
            await send_kafka_message(
                settings.KAFKA_TOPIC_STATUS,
                {"post_id": post_id, "status": "failed", "error": error_msg}
            )

    except ValueError as e: # Catch platform not found error
        logger.error(f"Platform '{platform_name}' not found for post {post_id}: {e}")
        await crud_post.update_post_status(db, post_id, status='failed', error_message=str(e))
        # Send failure status
        await send_kafka_message(
            settings.KAFKA_TOPIC_STATUS,
            {"post_id": post_id, "status": "failed", "error": f"Platform '{platform_name}' not supported."}
        )
    except Exception as exc:
        logger.exception(f"Task failed for post {post_id}: {exc}. Retrying...")
        try:
            # Retry the task with exponential backoff
            # The delay is default_retry_delay * 2 ** current_retry_count
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for post {post_id}. Marking as failed.")
            error_msg = f"Max retries exceeded: {exc}"
            await crud_post.update_post_status(db, post_id, status='failed', error_message=error_msg)
            # Send final failure status
            await send_kafka_message(
                settings.KAFKA_TOPIC_STATUS,
                {"post_id": post_id, "status": "failed", "error": error_msg}
            )
    finally:
        # Close DB connection if necessary
        # await db.client.close() # Example if using a client per task run
        pass


@cel.task
async def enqueue_due_posts():
    """
    Periodically fetches due posts from the database and enqueues them
    for sending via the 'send_post' task.

    TODO:
        - Implement proper async database operations.
        - Handle potential errors during fetching or task enqueueing.
        - Consider locking or status updates to prevent duplicate processing if this task runs concurrently.
    """
    logger.info("Task started: enqueue_due_posts")
    db = await get_db()
    try:
        due_posts = await crud_post.get_due_posts(db)
        logger.info(f"Found {len(due_posts)} posts due for sending.")

        for post in due_posts:
            logger.info(f"Enqueuing post {post.id} for platform {post.platform}")
            # Send task to the queue
            send_post.delay(
                post_id=str(post.id), # Ensure ID is serialized correctly (string)
                platform_name=post.platform,
                content=post.content
            )
            # Optional: Update post status to 'queued' or similar immediately
            # await crud_post.update_post_status(db, str(post.id), status='queued')

    except Exception as e:
        logger.exception(f"Error during enqueue_due_posts: {e}")
    finally:
        # Close DB connection if necessary
        # await db.client.close()
        pass

# Configure Celery Beat schedule
cel.conf.beat_schedule = {
    'enqueue-due-posts-every-minute': {
        'task': 'app.tasks.enqueue_due_posts',
        'schedule': crontab(minute='*'), # Run every minute
        # 'args': (arg1, arg2), # Add args if the task needs them
    },
}
