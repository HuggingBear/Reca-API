import os
import logging
import jwt
from datetime import datetime, timezone

def is_jwt_token_expired(token):
    """
    Checks if a JWT token has expired.
    Args:
        token (str): The JWT token to check.

    Returns:
        bool: True if the token has expired, False otherwise.

    Raises:
        jwt.InvalidTokenError: If the token is invalid.
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        exp = payload.get('exp')
        if exp:
            expiry_time = datetime.fromtimestamp(exp, tz=timezone.utc)
            if expiry_time < datetime.now(tz=timezone.utc):
                return True
        return False
    except jwt.InvalidTokenError:
        return True

def get_logging_level():
    if os.environ.get('ENVIRONMENT') == 'development':
        return logging.DEBUG
    else:
        return logging.INFO
        