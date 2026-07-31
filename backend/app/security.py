"""
security.py - Password hashing and JWT token helpers.

Two security ideas are used here:

1. Passwords are NEVER stored as plain text. We store a "hash" using the
   bcrypt algorithm. A hash is a one-way transformation, so even if the
   database is stolen, the passwords cannot be read. To check a login we
   hash the typed password and compare it with the stored hash.

2. After a successful login we issue a JWT (JSON Web Token). A JWT is a
   small, signed piece of text that proves "this user is logged in".
   The token carries the user id and role, and is signed with a secret
   key. On every protected request the client sends this token back in
   the "Authorization" header and we verify its signature.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import settings


def hash_password(password: str) -> str:
    """Turn a plain-text password into a secure bcrypt hash."""
    # gensalt() creates a random "salt" so two users with the same
    # password still get different hashes.
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Check a typed password against the stored hash.

    Returns True if they match, False otherwise.
    """
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: int, role: str) -> str:
    """Create a signed JWT that identifies a logged-in user."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),                                    # "subject" = user id
        "role": role,                                           # "patient" or "doctor"
        "iat": now,                                             # issued at
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),  # expiry
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def decode_access_token(token: str) -> dict:
    """Verify a JWT signature and return its payload.

    Raises jwt.PyJWTError if the token is invalid or expired.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
