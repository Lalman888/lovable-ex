import logging
from datetime import timedelta
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

# Assuming settings, security, and platforms are structured as previously defined
from app.config import settings
from app.security import (
    User, # Using the placeholder User from security.py for this focused task
    authenticate_user,
    create_access_token,
    get_current_active_user, # Use get_current_active_user for active user check
    oauth2_scheme # Not directly used in main's endpoints but good to have for context
)
from app.platforms import PLATFORM_MAP, get_platform # Import PLATFORM_MAP and get_platform

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Social Media Automation API",
    version="0.1.0",
    description="API for scheduling and publishing posts to various social media platforms. "
                "Provides authentication and platform management.",
    # swagger_ui_parameters={"defaultModelsExpandDepth": -1} # Optional: Hides schemas by default
)

# --- Pydantic Models for API ---
class Token(BaseModel):
    access_token: str
    token_type: str

class PlatformName(BaseModel):
    name: str

# --- Authentication Endpoint ---
@app.post("/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticates a user and returns an access token.

    Uses OAuth2 Password Flow. Provide username and password in form data.
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
    logger.info(f"Token issued for user: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}

# --- Sample Protected Endpoint ---
@app.get("/v1/hello", response_model=dict, tags=["Protected Example"])
async def read_hello(current_user: User = Depends(get_current_active_user)):
    """
    A sample protected endpoint that requires authentication.

    Returns a greeting to the authenticated user.
    """
    logger.info(f"User {current_user.username} accessed /v1/hello")
    return {"message": f"Hello {current_user.username}"}

# --- Platform Listing Endpoint ---
@app.get("/v1/platforms", response_model=List[PlatformName], tags=["Platforms"])
async def list_available_platforms():
    """
    Lists all available (configured) social media platforms.
    """
    platform_names = [{"name": name} for name in PLATFORM_MAP.keys()]
    logger.info(f"Available platforms requested. Returning: {platform_names}")
    return platform_names

# --- Example: Using a Platform (Conceptual, not a direct endpoint from prompt but shows usage) ---
# This is a conceptual example of how one might use the get_platform function.
# It's not requested as an endpoint in the prompt, but useful for context.
# @app.post("/v1/post_to_platform/{platform_name}", response_model=dict, tags=["Platforms"])
# async def post_to_specific_platform(
#     platform_name: str, 
#     content: dict, # This would be a Pydantic model
#     current_user: User = Depends(get_current_active_user) 
# ):
#     """
#     (Conceptual Example) Post content to a specified platform.
#     """
#     try:
#         platform_service = get_platform(platform_name)
#         logger.info(f"User {current_user.username} posting to {platform_name} via {platform_service}")
#         # Assume content is validated Pydantic model for the platform's requirements
#         result = platform_service.send(content) 
#         return {"platform": platform_name, "status": "success", "details": result}
#     except ValueError as e:
#         logger.error(f"Platform error: {e}")
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
#     except Exception as e:
#         logger.error(f"Error posting to platform {platform_name}: {e}")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to post to {platform_name}")


@app.get("/", tags=["Public"])
async def read_root():
    """
    Root endpoint providing a welcome message.
    """
    return {"message": "Welcome to the Social Media Automation API!"}

# --- TODOs from original scaffold might still apply ---
# - Add more robust error handling and logging.
# - Secure the API further (rate limiting, input validation beyond Pydantic).
# - Add API routes for managing users, viewing post statuses, etc.
# - Configure CORS if the frontend is served from a different origin.
# - Add tests for all endpoints and logic.
# - Integrate actual database for users and posts instead of placeholders.
# - Integrate actual Kafka/Celery for scheduling if that was part of a larger plan.
