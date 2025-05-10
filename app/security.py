from datetime import datetime, timedelta
from typing import Optional, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config import settings
# Placeholder for user model and user fetching function
# from app.models.user import User # Assuming you have a User model
# from app.crud.user import get_user_by_username # Assuming a function to fetch user

# --- Configuration ---
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# OAuth2PasswordBearer for token handling in FastAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Pydantic Models ---
class TokenData(BaseModel):
    username: Optional[str] = None

# Placeholder User model - replace with your actual User model from app.models.user
class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    hashed_password: Optional[str] = None # Ensure your user model in DB has this

# Placeholder for fetching user from DB - replace with app.crud.user.get_user
# This is a simplified in-memory store for demonstration
fake_users_db = {
    "testuser": {
        "username": "testuser",
        "full_name": "Test User",
        "email": "test@example.com",
        "hashed_password": pwd_context.hash("password123"), # Store hashed password
        "disabled": False,
    }
}

def get_user_from_db(username: str) -> Optional[User]:
    # TODO: Replace this with actual database lookup from app.crud.user.get_user
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return User(**user_dict)
    return None


# --- Password Utilities ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    # TODO: This function should ideally be part of user creation logic in crud.user
    return pwd_context.hash(password)


# --- Token Utilities ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- User Authentication ---
async def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authenticates a user by username and password.
    Returns the user object if authentication is successful, otherwise None.
    """
    # TODO: Replace with actual user fetching from app.crud.user.get_user
    user = get_user_from_db(username)
    if not user:
        return None
    if not user.hashed_password or not verify_password(password, user.hashed_password):
        return None
    return user


# --- Current User Dependency ---
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """
    Dependency to get the current authenticated user.
    Decodes the JWT token, validates it, and fetches the user.
    Raises HTTPException if authentication fails.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    # TODO: Replace with actual user fetching from app.crud.user.get_user
    user = get_user_from_db(token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """
    Dependency to get the current active authenticated user.
    Checks if the user is disabled.
    """
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user
