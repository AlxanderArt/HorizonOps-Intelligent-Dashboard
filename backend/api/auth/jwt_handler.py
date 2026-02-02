"""
JWT Authentication Handler
Handles token creation, validation, and user authentication
"""

from datetime import datetime, timedelta
from typing import Optional
import jwt
from jwt.exceptions import PyJWTError as JWTError
from pydantic import BaseModel
import hashlib
import os

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "horizonops-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def get_password_hash(password: str) -> str:
    """Hash password using SHA256 (use bcrypt in production)."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return get_password_hash(plain_password) == hashed_password


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class User(BaseModel):
    username: str
    email: str
    full_name: str
    role: str
    disabled: bool = False


class UserInDB(User):
    hashed_password: str


# Simulated user database (replace with real DB in production)
USERS_DB = {
    "admin": {
        "username": "admin",
        "email": "admin@horizonops.io",
        "full_name": "System Administrator",
        "role": "admin",
        "hashed_password": get_password_hash("admin123"),
        "disabled": False,
    },
    "operator": {
        "username": "operator",
        "email": "operator@horizonops.io",
        "full_name": "Machine Operator",
        "role": "operator",
        "hashed_password": get_password_hash("operator123"),
        "disabled": False,
    },
    "viewer": {
        "username": "viewer",
        "email": "viewer@horizonops.io",
        "full_name": "Dashboard Viewer",
        "role": "viewer",
        "hashed_password": get_password_hash("viewer123"),
        "disabled": False,
    },
}


def get_user(username: str) -> Optional[UserInDB]:
    """Retrieve a user from the database."""
    if username in USERS_DB:
        user_dict = USERS_DB[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user with username and password."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": "horizonops"
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            return None
        return TokenData(username=username, role=role)
    except JWTError:
        return None
