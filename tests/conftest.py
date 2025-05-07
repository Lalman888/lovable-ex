import pytest
import pytest_asyncio # Required for async fixtures
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi.testclient import TestClient
from testcontainers.mongodb import MongoDbContainer
from testcontainers.redis import RedisContainer
from testcontainers.kafka import KafkaContainer

# Import your FastAPI application and settings
from app.main import app # Assuming your FastAPI app instance is here
from app.config import settings, Settings # Import the actual settings object and class

# --- Test Container Fixtures ---

@pytest.fixture(scope="session")
def mongo_container():
    """Starts a MongoDB container for the test session."""
    with MongoDbContainer("mongo:6") as mongo:
        yield mongo.get_connection_url()

@pytest.fixture(scope="session")
def redis_container():
    """Starts a Redis container for the test session."""
    with RedisContainer("redis:7") as redis:
        # Construct the redis URL format
        host = redis.get_container_host_ip()
        port = redis.get_exposed_port(redis.port)
        redis_url = f"redis://{host}:{port}/0"
        yield redis_url

@pytest.fixture(scope="session")
def kafka_container():
    """
    Starts a Kafka container (which includes Zookeeper) for the test session.
    Using Confluent image as it's common. Adjust image name if needed.
    """
    # Note: KafkaContainer often uses Confluent images internally.
    # Check testcontainers documentation if specific image version is critical.
    with KafkaContainer(image="confluentinc/cp-kafka:latest") as kafka:
        yield kafka.get_bootstrap_server()


# --- Settings Override Fixture ---

@pytest.fixture(scope="session", autouse=True) # Autouse ensures it applies to all tests
def settings_override(mongo_container, redis_container, kafka_container):
    """
    Overrides application settings to use test container URLs for the entire session.
    This uses monkeypatching on the *instance* of settings used by the app.
    """
    original_mongo_uri = settings.MONGO_URI
    original_redis_url = settings.REDIS_URL
    original_kafka_servers = settings.KAFKA_BOOTSTRAP_SERVERS
    original_elastic_url = settings.ELASTIC_URL

    settings.MONGO_URI = mongo_container + "/testdb" # Use a specific test DB name
    settings.REDIS_URL = redis_container
    settings.KAFKA_BOOTSTRAP_SERVERS = kafka_container
    settings.ELASTIC_URL = None # Disable Elasticsearch logging for tests unless needed

    print(f"Overriding settings:\n"
          f"  MONGO_URI={settings.MONGO_URI}\n"
          f"  REDIS_URL={settings.REDIS_URL}\n"
          f"  KAFKA_BOOTSTRAP_SERVERS={settings.KAFKA_BOOTSTRAP_SERVERS}\n"
          f"  ELASTIC_URL={settings.ELASTIC_URL}")

    yield # Let the test session run with overridden settings

    # Restore original settings after tests
    settings.MONGO_URI = original_mongo_uri
    settings.REDIS_URL = original_redis_url
    settings.KAFKA_BOOTSTRAP_SERVERS = original_kafka_servers
    settings.ELASTIC_URL = original_elastic_url
    print("Restored original settings.")


# --- Database Client Fixture ---

@pytest_asyncio.fixture(scope="function") # Function scope to get clean DB for each test
async def db_client(settings_override, mongo_container):
    """
    Provides an AsyncIOMotorClient connected to the test MongoDB container.
    Includes database cleanup after each test function.
    """
    # mongo_container fixture provides the base URL
    # settings_override ensures settings.MONGO_URI points to the test container + /testdb
    test_db_name = settings.MONGO_URI.split("/")[-1] # Extract test DB name
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[test_db_name]
    print(f"Using test database: {test_db_name}")

    yield db # Provide the database object to the test

    print(f"Dropping test database: {test_db_name}")
    await client.drop_database(test_db_name)
    client.close()


# --- FastAPI Test Client Fixture ---

@pytest.fixture(scope="session")
def test_client(settings_override):
    """
    Provides a FastAPI TestClient instance configured for the application.
    Uses the settings overridden by settings_override.
    """
    # The app should automatically use the overridden settings instance
    with TestClient(app) as client:
        yield client

# TODO:
# - Add fixtures for creating test users or other prerequisite data.
# - Consider fixtures for mocking external services not covered by containers (e.g., email).
# - If Celery results are needed, ensure the backend (Redis) is configured correctly via settings_override.
