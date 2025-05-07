import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock

from celery.exceptions import Retry

# Import the Celery app instance and the task to test
from app.tasks import cel, send_post
from app.models.post import PostInDB # For creating test data or checking DB state

# Assuming fixtures like db_client are available from conftest.py

# --- Test Data ---
TEST_POST_ID = "605c72cfd5e0a6a7b8d9c8a1" # Example valid ObjectId string
TEST_PLATFORM = "twitter"
TEST_CONTENT = {"text": "This is a test tweet task"}

@pytest_asyncio.fixture(scope="function")
async def setup_test_post(db_client):
    """Fixture to insert a dummy post into the test DB before a task test."""
    post_doc = {
        "_id": pytest.importorskip("bson").ObjectId(TEST_POST_ID),
        "user_id": "test_user",
        "platform": TEST_PLATFORM,
        "content": TEST_CONTENT,
        "scheduled_time": None,
        "status": "pending", # Initial state before task runs
        "created_at": pytest.importorskip("datetime").datetime.utcnow(),
        "updated_at": pytest.importorskip("datetime").datetime.utcnow(),
    }
    result = await db_client["posts"].insert_one(post_doc)
    print(f"Inserted test post with ID: {result.inserted_id}")
    yield str(result.inserted_id) # Provide the ID to the test
    # Cleanup happens in db_client fixture


@pytest.mark.asyncio
@patch("app.tasks.get_platform") # Mock the platform factory
@patch("app.tasks.crud_post.update_post_status", new_callable=AsyncMock) # Mock the DB update function
@patch("app.tasks.send_kafka_message", new_callable=AsyncMock) # Mock the Kafka status update
async def test_send_post_success(
    mock_send_kafka, mock_update_status, mock_get_platform,
    db_client, setup_test_post # Use DB client and setup fixture
):
    """Tests the successful execution of the send_post task."""
    post_id = setup_test_post # Get the ID of the post created by the fixture

    # Configure the mock platform
    mock_platform_instance = AsyncMock()
    mock_platform_instance.send.return_value = {"success": True, "post_id": "platform_123"}
    mock_get_platform.return_value = mock_platform_instance

    # --- Execute the task ---
    # Use .s() to create signature and .apply() to run synchronously in the test process
    # Note: Celery task functions are often async now, ensure test runner handles it.
    # If the task function itself is async, we might need to await its execution directly
    # or use a testing backend that supports async tasks.
    # For simplicity, let's assume we can await the task function directly here for testing purposes
    # (This might require adjustments based on Celery test setup)
    # Alternatively, mock the async parts within the task if direct await isn't feasible.

    # Direct await (if test setup allows calling the async task function directly)
    await send_post(post_id=post_id, platform_name=TEST_PLATFORM, content=TEST_CONTENT)

    # --- Assertions ---
    # 1. Assert platform was fetched and send was called
    mock_get_platform.assert_called_once_with(TEST_PLATFORM)
    mock_platform_instance.send.assert_called_once_with(TEST_CONTENT)

    # 2. Assert DB status updates
    assert mock_update_status.call_count == 2 # processing, then posted
    # Check the calls were made with correct arguments
    mock_update_status.assert_any_call(db_client, post_id, status='processing')
    mock_update_status.assert_any_call(db_client, post_id, status='posted')
    # Optionally, check the actual DB state (though mocking update might be sufficient)
    # final_post_doc = await db_client["posts"].find_one({"_id": pytest.importorskip("bson").ObjectId(post_id)})
    # assert final_post_doc["status"] == "posted"

    # 3. Assert Kafka status update was sent
    mock_send_kafka.assert_called_once_with(
        pytest.importorskip("app.config").settings.KAFKA_TOPIC_STATUS,
        {"post_id": post_id, "status": "posted", "platform_post_id": "platform_123"}
    )


@pytest.mark.asyncio
@patch("app.tasks.get_platform")
@patch("app.tasks.crud_post.update_post_status", new_callable=AsyncMock)
@patch("app.tasks.send_kafka_message", new_callable=AsyncMock)
@patch("celery.app.task.Task.retry") # Mock the retry method of the base Task class
async def test_send_post_retry(
    mock_task_retry, mock_send_kafka, mock_update_status, mock_get_platform,
    db_client, setup_test_post
):
    """Tests that the send_post task retries on platform failure."""
    post_id = setup_test_post

    # Configure the mock platform to raise an error
    mock_platform_instance = AsyncMock()
    mock_platform_instance.send.side_effect = Exception("Simulated API Error")
    mock_get_platform.return_value = mock_platform_instance

    # Configure the mock retry method to raise the Retry exception Celery expects
    mock_task_retry.side_effect = Retry()

    # --- Execute the task ---
    # We expect the task to catch the exception from platform.send and call self.retry()
    # Need to wrap the call in pytest.raises to catch the Retry exception raised by the mock
    with pytest.raises(Retry):
         # Direct await for testing (adjust if needed)
        await send_post(post_id=post_id, platform_name=TEST_PLATFORM, content=TEST_CONTENT)

    # --- Assertions ---
    # 1. Assert platform was fetched and send was called
    mock_get_platform.assert_called_once_with(TEST_PLATFORM)
    mock_platform_instance.send.assert_called_once_with(TEST_CONTENT)

    # 2. Assert DB status was updated to 'processing' (but not 'failed' yet due to retry)
    mock_update_status.assert_called_once_with(db_client, post_id, status='processing')
    # Check actual DB state if needed
    # current_post_doc = await db_client["posts"].find_one({"_id": pytest.importorskip("bson").ObjectId(post_id)})
    # assert current_post_doc["status"] == "processing" # Should still be processing

    # 3. Assert Kafka status update was NOT sent yet
    mock_send_kafka.assert_not_called()

    # 4. Assert the task's retry method was called
    # The mock_task_retry defined above should have been called.
    # We might need to inspect the call args if specific retry parameters matter.
    mock_task_retry.assert_called_once()


# TODO: Add more task tests:
# - Test max retries exceeded scenario (mock self.retry to raise MaxRetriesExceededError).
# - Test handling of unsupported platform (ValueError from get_platform).
# - Test the `enqueue_due_posts` task (requires mocking `crud_post.get_due_posts` and `send_post.delay`).
# - Test tasks with different content types or platform variations.
