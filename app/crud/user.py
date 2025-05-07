from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.models.user import UserCreate, UserInDB
from app.security import get_password_hash
from app.config import settings

# Assume db is an instance of AsyncIOMotorDatabase passed or available globally/contextually

async def get_db() -> AsyncIOMotorDatabase:
    """Dependency to get DB instance (replace with your actual DB connection setup)."""
    # This is a placeholder. In a real app, manage the client connection lifecycle.
    client = AsyncIOMotorClient(settings.MONGO_URI)
    return client.get_database("mydatabase") # Replace "mydatabase" if needed

async def get_user(db: AsyncIOMotorDatabase, username: str) -> Optional[UserInDB]:
    """
    Retrieves a user from the database by username.

    Args:
        db: The database instance.
        username: The username to search for.

    Returns:
        The UserInDB object if found, otherwise None.

    TODO:
        - Implement the database query logic using motor to find a user by username.
        - Handle the case where the user is not found.
    """
    # Example query (adapt as needed):
    # user_doc = await db["users"].find_one({"username": username})
    # if user_doc:
    #     return UserInDB(**user_doc)
    # return None

    print(f"CRUD: Simulating fetching user '{username}'")
    # Placeholder return - replace with actual logic
    if username == "testuser": # Simulate finding a user
         return UserInDB(
             _id="605c72cfd5e0a6a7b8d9c8a1", # Example ObjectId string
             username="testuser",
             email="test@example.com",
             hashed_password=get_password_hash("password"), # Example hashed password
             is_active=True
         )
    return None

async def create_user(db: AsyncIOMotorDatabase, user: UserCreate) -> UserInDB:
    """
    Creates a new user in the database.

    Args:
        db: The database instance.
        user: The user data to create.

    Returns:
        The created UserInDB object.

    TODO:
        - Implement the database insertion logic using motor.
        - Hash the password before storing.
        - Handle potential database errors (e.g., duplicate username/email).
    """
    hashed_password = get_password_hash(user.password)
    user_doc = UserInDB(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=user.is_active
        # Let MongoDB generate the _id
    )
    # Example insertion (adapt as needed):
    # result = await db["users"].insert_one(user_doc.dict(by_alias=True, exclude={'id'})) # Exclude None id
    # created_user = await db["users"].find_one({"_id": result.inserted_id})
    # return UserInDB(**created_user)

    print(f"CRUD: Simulating user creation for '{user.username}'")
    # Placeholder return
    return user_doc # Return the constructed object for now
