import hashlib
import hmac
import os
import secrets
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.models import LoginEvent, User
from app import redis_client as store
from app.services.email_service import send_otp_email

OTP_DEV_MODE = os.getenv("OTP_DEV_MODE", "true").lower() == "true"


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1, dklen=32)
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, AttributeError):
        return False


def log_event(db: Session, username: str, event: str) -> None:
    """Records sign-in activity for the audit view. Must never break a login."""
    try:
        db.add(LoginEvent(username=username[:254], event=event))
        db.commit()
    except Exception:
        db.rollback()


def mask_email(email):
    if not email or "@" not in email:
        return None
    name, domain = email.split("@", 1)
    return name[:2] + "*" * max(len(name) - 2, 1) + "@" + domain


# Used so a wrong username costs the same time as a wrong password
_DUMMY_HASH = hash_password("not-a-real-password")


def deliver_otp(username: str, otp: str):
    print(f"[OTP] Login code for '{username}': {otp}  (valid {store.OTP_TTL_SECONDS // 60} min)", flush=True)


class AuthService:
    @staticmethod
    def register(db: Session, username: str, password: str, email: str) -> User:
        if db.query(User).filter(User.username == username).first():
            raise HTTPException(status_code=409, detail="That username is already taken.")
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=409, detail="That email is already registered.")
        user = User(username=username, email=email, password_hash=hash_password(password))
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="That username or email is already taken.")
        db.refresh(user)
        return user

    @staticmethod
    def start_login(db: Session, identifier: str, password: str) -> dict:
        if store.is_login_locked(identifier):
            log_event(db, identifier, "login blocked (too many failures)")
            raise HTTPException(status_code=429, detail="Too many failed attempts. Try again in a few minutes.")

        column = User.email if "@" in identifier else User.username
        user = db.query(User).filter(column == identifier).first()
        stored = user.password_hash if user and user.password_hash else _DUMMY_HASH
        if not (verify_password(password, stored) and user and user.password_hash):
            store.record_login_failure(identifier)
            log_event(db, identifier, "wrong password")
            raise HTTPException(status_code=401, detail="Wrong username/email or password.")

        username = user.username
        store.clear_login_failures(identifier)
        otp = f"{secrets.randbelow(10**6):06d}"
        store.save_otp(username, otp)

        if user.email:
            if not send_otp_email(user.email, otp, user.username):
                store.delete_otp(username)
                log_event(db, username, "code email failed")
                raise HTTPException(status_code=502, detail="Could not send the email. Please try again shortly.")
        else:
            deliver_otp(username, otp)
        log_event(db, username, "password ok, code sent")

        response = {"otp_required": True, "expires_in": store.OTP_TTL_SECONDS, "email_hint": mask_email(user.email), "username": username}
        if OTP_DEV_MODE:
            response["dev_otp"] = otp
        return response

    @staticmethod
    def finish_login(db: Session, username: str, otp: str) -> dict:
        result = store.check_otp(username, otp)
        if result != "ok":
            log_event(db, username, {"expired": "code expired", "locked": "code attempts exhausted", "invalid": "wrong code"}.get(result, result))
        if result == "expired":
            raise HTTPException(status_code=400, detail="That code expired. Please log in again.")
        if result == "locked":
            raise HTTPException(status_code=429, detail="Too many wrong codes. Please log in again.")
        if result == "invalid":
            raise HTTPException(status_code=401, detail="Incorrect code.")

        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="Account not found.")
        log_event(db, username, "logged in")
        return {"token": store.create_session(user.id), "username": user.username}
