import logging
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from prometheus_client import Counter, Histogram # Import if used directly here

from app.config import settings
from app.security import authenticate_user, create_access_token, get_current_user
from app.models.user import User, UserInDB
from app.models.post import SchedulePostRequest, SchedulePostResponse
from app.crud import post as crud_post
from app.crud.post import get_db as get_post_db # Specific import if needed
from app.messaging import producer as kafka_producer
from app.metrics import metrics_app, POSTS_SCHEDULED, SCHEDULE_REQUEST_LATENCY # Import metrics and the ASGI app
from app.logging_config import setup_elasticsearch_logging

# --- Logging Setup ---
# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup Elasticsearch logging (optional, based on config)
# setup_elasticsearch_logging() # Call this if you want ES logging for the main app

# --- Application Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application startup...")
    # Initialize Kafka Producer
    await kafka_producer.get_producer()
    # Initialize database connections (if managed globally)
    # setup_elasticsearch_logging() # Or setup logging here
    yield
    # Shutdown
    logger.info("Application shutdown...")
    await kafka_producer.stop_producer()
    # Close database connections

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Social Media Scheduler API",
    version="0.1.0",
    description="API to schedule posts on various social media platforms.",
    lifespan=lifespan # Use the lifespan context manager
)

# --- Authentication Endpoint ---
@app.post("/token", response_model=dict) # Define a response model for the token if desired
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Provides an access token for valid user credentials.
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Scheduling Endpoint ---
@app.post("/v1/schedule", response_model=SchedulePostResponse, status_code=status.HTTP_202_ACCEPTED)
async def schedule_post(
    post_request: SchedulePostRequest,
    current_user: User = Depends(get_current_user), # Dependency Injection for auth
    db = Depends(get_post_db) # Dependency Injection for DB session
):
    """
    Schedules a post to be sent to a specified platform.

    Requires authentication.
    """
    start_time = time.time() # For latency metric

    try:
        # 1. Create the post record in the database
        # TODO: Ensure user_id from current_user is correctly passed if needed by CRUD
        # Assuming user ID is part of the User model returned by get_current_user
        created_post = await crud_post.create_scheduled_post(db, user_id=str(current_user.id), post_data=post_request)
        post_id = str(created_post.id) # Ensure ID is string for Kafka/response
        logger.info(f"Post record created with ID: {post_id} by user {current_user.username}")

        # 2. Send message to Kafka for the worker to pick up
        # TODO: Decide exactly what info the worker needs via Kafka
        # Sending minimal info: post_id, platform, content
        kafka_message = {
            "post_id": post_id,
            "platform": post_request.platform,
            "content": post_request.content,
            "scheduled_time": post_request.scheduled_time.isoformat() if post_request.scheduled_time else None,
            "user_id": str(current_user.id) # Optional: include user ID if worker needs it
        }
        await kafka_producer.send(settings.KAFKA_TOPIC_REQUEST, kafka_message)
        logger.info(f"Message sent to Kafka topic '{settings.KAFKA_TOPIC_REQUEST}' for post ID: {post_id}")

        # 3. Update metrics
        POSTS_SCHEDULED.labels(platform=post_request.platform).inc()

        # 4. Prepare and return the response
        response = SchedulePostResponse(
            post_id=post_id,
            # Status might initially be 'pending' or 'queued' based on design
            status=created_post.status,
            message=f"Post for {post_request.platform} scheduled successfully."
        )
        return response

    except ValueError as ve: # Example: Catch specific errors like invalid platform
         logger.error(f"Scheduling error: {ve}")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        # TODO: Implement more specific error handling
        logger.exception(f"Failed to schedule post for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to schedule post")
    finally:
        # Record latency metric regardless of success or failure
        latency = time.time() - start_time
        SCHEDULE_REQUEST_LATENCY.labels(method='POST').observe(latency)


# --- Metrics Endpoint ---
# Mount the ASGI app provided by prometheus_client to expose metrics
app.mount("/metrics", metrics_app)
logger.info("Metrics endpoint /metrics configured.")

# --- Example Protected Endpoint ---
@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Returns the details of the currently authenticated user.
    """
    return current_user


# --- Root Endpoint ---
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Social Media Scheduler API"}

# --- TODO ---
# - Implement proper database session management (e.g., using FastAPI dependencies). Done via Depends(get_post_db)
# - Add more robust error handling and logging.
# - Secure the API further (rate limiting, input validation beyond Pydantic).
# - Add API routes for managing users, viewing post statuses, etc.
# - Configure CORS if the frontend is served from a different origin.
# - Add tests for all endpoints and logic.

# Import time for latency calculation
import time
