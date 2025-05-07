from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from app.config import settings
from app.models.user import UserInDB # Assuming UserInDB will be defined here or imported
from app.crud import user as crud_user # Assuming crud functions will be available

# Password Hashing Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token") # Matches the endpoint in main.py

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

async def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """
    Authenticates a user by username and password.

    Args:
        username: The username to authenticate.
        password: The password to verify.

    Returns:
        The user object if authentication is successful, otherwise None.

    TODO:
        - Fetch user from the database using `crud_user.get_user`.
        - Handle user not found scenario.
    """
    user = await crud_user.get_user(username=username) # Placeholder
    if not user:
        return None
    if not verify_password(password, user.hashed_password): # Assuming UserInDB has hashed_password
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a JWT access token.

    Args:
        data: The data payload to include in the token (e.g., {'sub': username}).
        expires_delta: Optional timedelta object for token expiry. Defaults to
                       ACCESS_TOKEN_EXPIRE_MINUTES from settings.

    Returns:
        The encoded JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """
    Dependency to get the current authenticated user from the token.

    Args:
        token: The OAuth2 token extracted from the request header.

    Returns:
        The authenticated user object.

    Raises:
        HTTPException: If the token is invalid, expired, or the user doesn't exist.

    TODO:
        - Handle JWTError during decoding.
        - Fetch user from the database based on the username in the token payload.
        - Handle user not found scenario after successful token validation.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        # Here you might want to add token validation logic (e.g., check token blacklist)
    except JWTError:
        raise credentials_exception

    user = await crud_user.get_user(username=username) # Placeholder
    if user is None:
        raise credentials_exception
    return user

# Optional: Dependency for getting the current active user (if you add an is_active flag)
# async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
#     if not current_user.is_active: # Requires an 'is_active' field in UserInDB
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user
