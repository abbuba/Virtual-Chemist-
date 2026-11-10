import hashlib
import hmac
import os
import secrets
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Redis client with connection pooling
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def update_workspace_atom(session_id: str, atom_id: str, x: float, y: float):
    """Caches atom spatial coordinates in Redis hash for sub-millisecond lookups."""
    key = f"workspace:{session_id}:atoms"
    redis_client.hset(key, atom_id, f"{x},{y}")
    redis_client.expire(key, 3600)  # Expire session after 1 hour of inactivity

def get_workspace_atoms(session_id: str) -> dict:
    """Retrieves all active atom coordinates for a user session."""
    key = f"workspace:{session_id}:atoms"
    raw_data = redis_client.hgetall(key)
    # Parse coordinates back into floats
    return {atom_id: list(map(float, coords.split(','))) for atom_id, coords in raw_data.items()}

def remove_workspace_atom(session_id: str, atom_id: str):
    """Removes an atom when it's consumed in a molecular bond."""
    key = f"workspace:{session_id}:atoms"
    redis_client.hdel(key, atom_id)

OTP_TTL_SECONDS = 300
OTP_MAX_ATTEMPTS = 5
LOGIN_MAX_FAILURES = 5
LOGIN_FAIL_WINDOW = 900
SESSION_TTL_SECONDS = 86400


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def save_otp(username: str, otp: str):
    key = f"otp:{username}"
    redis_client.delete(key + ":attempts")
    redis_client.set(key, _digest(otp), ex=OTP_TTL_SECONDS)


def check_otp(username: str, otp: str) -> str:
    """Returns 'ok', 'invalid', 'expired' or 'locked'. A correct code works once."""
    key = f"otp:{username}"
    stored = redis_client.get(key)
    if stored is None:
        return "expired"
    attempts_key = key + ":attempts"
    if int(redis_client.get(attempts_key) or 0) >= OTP_MAX_ATTEMPTS:
        redis_client.delete(key, attempts_key)
        return "locked"
    if hmac.compare_digest(stored, _digest(otp)):
        redis_client.delete(key, attempts_key)
        return "ok"
    redis_client.incr(attempts_key)
    redis_client.expire(attempts_key, OTP_TTL_SECONDS)
    return "invalid"


def is_login_locked(username: str) -> bool:
    return int(redis_client.get(f"loginfail:{username}") or 0) >= LOGIN_MAX_FAILURES


def record_login_failure(username: str):
    key = f"loginfail:{username}"
    redis_client.incr(key)
    redis_client.expire(key, LOGIN_FAIL_WINDOW)


def clear_login_failures(username: str):
    redis_client.delete(f"loginfail:{username}")


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    redis_client.set(f"session:{_digest(token)}", user_id, ex=SESSION_TTL_SECONDS)
    return token


def get_session_user_id(token: str):
    value = redis_client.get(f"session:{_digest(token)}")
    return int(value) if value else None


def delete_session(token: str):
    redis_client.delete(f"session:{_digest(token)}")


def delete_otp(username: str):
    redis_client.delete(f"otp:{username}", f"otp:{username}:attempts")
