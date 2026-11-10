import re
from pydantic import BaseModel, Field, field_validator

USERNAME_RE = re.compile(r"^[a-z0-9_]{3,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _clean_username(value: str) -> str:
    return value.strip().lower()


class RegisterRequest(BaseModel):
    username: str
    password: str = Field(..., min_length=8, max_length=128)
    email: str = Field(..., max_length=254)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not EMAIL_RE.match(value):
            raise ValueError("Please enter a valid email address.")
        return value

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = _clean_username(value)
        if not USERNAME_RE.match(value):
            raise ValueError("Username must be 3-30 characters: letters, numbers or underscore.")
        return value


class LoginRequest(BaseModel):
    identifier: str = Field(..., max_length=254)
    password: str = Field(..., max_length=128)

    @field_validator("identifier")
    @classmethod
    def clean(cls, value: str) -> str:
        return _clean_username(value)


class OtpRequest(BaseModel):
    username: str = Field(..., max_length=50)
    otp: str = Field(..., pattern=r"^\d{6}$")

    @field_validator("username")
    @classmethod
    def clean(cls, value: str) -> str:
        return _clean_username(value)
