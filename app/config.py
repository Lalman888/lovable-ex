from pydantic import BaseSettings, Field, MongoDsn, AnyHttpUrl
from typing import List, Optional

class Settings(BaseSettings):
    # Security
    SECRET_KEY: str = Field(...)
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # MongoDB
    MONGO_URI: MongoDsn

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = Field(...)
    KAFKA_TOPIC_REQUEST: str = Field(default="task_requests")
    KAFKA_TOPIC_STATUS: str = Field(default="task_status")

    # Redis (Celery Broker/Backend)
    REDIS_URL: str = Field(default="redis://redis:6379/0") # Using Redis URL format

    # Elasticsearch
    ELASTIC_URL: Optional[AnyHttpUrl] # Optional as it might not always be configured

    # Prometheus (for multi-process Uvicorn workers)
    PROMETHEUS_MULTIPROC_DIR: Optional[str] # Directory for multiprocess metrics

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()
