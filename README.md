# Social Media Automation Platform

## Project Overview

This project provides a robust platform for scheduling and automating social media posts across various platforms. It utilizes a microservices-oriented architecture built with modern Python technologies.

The core components include:

*   **FastAPI Backend**: Handles API requests, user authentication, and scheduling logic.
*   **Celery Workers**: Perform the actual task of posting to social media platforms asynchronously.
*   **Kafka**: Acts as a message broker for decoupling the API from the workers, handling task requests and status updates.
*   **MongoDB**: Serves as the primary database for storing user information, scheduled posts, and statuses.
*   **Redis**: Used as the Celery message broker and result backend.
*   **Elasticsearch**: Aggregates logs from different services for centralized monitoring and analysis (via Kibana).
*   **Prometheus & Grafana**: Provide monitoring and visualization of application metrics.
*   **Docker Compose**: Orchestrates the deployment and networking of all services for local development and testing.

## Features

*   Asynchronous post scheduling and execution.
*   Scalable architecture using message queues and task workers.
*   Centralized logging and monitoring.
*   Containerized deployment for easy setup.
*   Technology Stack:
    *   Backend: FastAPI
    *   Task Queue: Celery
    *   Messaging: Kafka
    *   Database: MongoDB
    *   Cache/Broker: Redis
    *   Logging: Elasticsearch & Kibana
    *   Monitoring: Prometheus & Grafana
    *   Containerization: Docker & Docker Compose

## Prerequisites

*   Docker: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)
*   Docker Compose: [https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/) (Often included with Docker Desktop)

## Environment Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url> # Replace with your repository URL
    cd <repository_directory>
    ```

2.  **Configure Environment Variables:**
    Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file:
    *   **`SECRET_KEY`**: **MUST** be set to a strong, unique secret string for security.
    *   `MONGO_URI`: Defaults to `mongodb://mongo:27017/mydatabase` (connects to the Mongo Docker service). Change `mydatabase` if needed.
    *   `KAFKA_BOOTSTRAP_SERVERS`: Defaults to `kafka:9092` (connects to the Kafka Docker service).
    *   `REDIS_URL`: Defaults to `redis://redis:6379/0` (connects to the Redis Docker service).
    *   `ELASTIC_URL`: Defaults to `http://elasticsearch:9200` (connects to the Elasticsearch Docker service).
    *   Other variables like `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `KAFKA_TOPIC_*` have defaults but can be adjusted if necessary.

## Running Locally

To build the Docker images and start all the services defined in `docker-compose.yml`:

```bash
docker-compose up --build -d
```

Once the services are running, you can access them at the following URLs:

*   **API**: [http://localhost:8000](http://localhost:8000)
*   **API Interactive Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Kafka UI (Offset Explorer/etc.)**: [http://localhost:8080](http://localhost:8080)
*   **Kibana (Logs & ES UI)**: [http://localhost:5601](http://localhost:5601)
*   **Prometheus (Metrics)**: [http://localhost:9090](http://localhost:9090)
*   **Grafana (Metrics Dashboard)**: [http://localhost:3000](http://localhost:3000) (Default Login: `admin` / `admin`)
*   **Flower (Celery Monitor)**: [http://localhost:5555](http://localhost:5555)

To stop the services:

```bash
docker-compose down
```

## Running Tests

The project includes a Continuous Integration (CI) workflow defined in `.github/workflows/ci.yml`, which automatically runs linters and tests on push/pull request events.

To run tests locally:

1.  **Set up a virtual environment (optional but recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run tests:**
    The test suite uses `pytest` and `testcontainers` to automatically spin up temporary Docker containers for MongoDB, Redis, and Kafka during the test run. Ensure Docker is running.
    ```bash
    pytest -v tests/
    ```

## API Endpoints

*   **`/token`** (POST)
    *   Authenticates a user and returns a JWT access token.
    *   Expects `application/x-www-form-urlencoded` data with `username` and `password` fields.
*   **`/v1/schedule`** (POST)
    *   Schedules a new post for asynchronous processing.
    *   Requires authentication (Bearer token in `Authorization` header).
    *   Expects a JSON body defining the `platform`, `content`, and optional `scheduled_time`.
    *   See [http://localhost:8000/docs](http://localhost:8000/docs) for detailed request/response schemas.
*   **`/metrics`** (GET)
    *   Exposes application metrics in Prometheus format for scraping.

## Deployment

(TBD) - Deployment instructions for production environments (e.g., Kubernetes manifests, cloud-specific guides) will be added here.

## Project Structure

```
.
├── .env.example          # Example environment variables
├── .github/workflows/    # GitHub Actions CI workflows
│   └── ci.yml
├── app/                  # Main Python application source code
│   ├── crud/             # Database interaction logic (Create, Read, Update, Delete)
│   ├── messaging/        # Kafka producer/consumer logic
│   ├── models/           # Pydantic data models (API requests/responses, DB models)
│   ├── platforms/        # Platform-specific posting logic (Twitter, Facebook, etc.)
│   ├── __init__.py
│   ├── config.py         # Application settings configuration (Pydantic)
│   ├── Dockerfile        # Dockerfile for the Python application image
│   ├── logging_config.py # Logging setup (including Elasticsearch)
│   ├── main.py           # FastAPI application entry point and API routes
│   ├── metrics.py        # Prometheus metrics definitions
│   ├── security.py       # Authentication and authorization logic
│   └── tasks.py          # Celery task definitions
├── docker-compose.yml    # Docker Compose configuration for all services
├── prometheus.yml        # Prometheus scrape configuration
├── README.md             # This file
├── requirements.txt      # Python package dependencies
└── tests/                # Application tests
    ├── __init__.py
    ├── conftest.py       # Pytest fixtures (including testcontainers setup)
    ├── test_api.py       # API endpoint tests
    └── test_tasks.py     # Celery task tests
```
