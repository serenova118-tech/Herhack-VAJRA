import re
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

# Conservative check; also rejects characters that could alter a URL path.
_EMAIL_OK = re.compile(r"^[^@\s/\\?#%]+@[^@\s/\\?#%]+\.[^@\s/\\?#%]{2,}$")


class FootprintRequest(BaseModel):
    email: Optional[str] = Field(default=None, max_length=254)
    username: Optional[str] = Field(default=None, max_length=80)
    profile_url: Optional[str] = Field(default=None, max_length=500)

    @field_validator("email")
    @classmethod
    def clean_email(cls, value):
        value = (value or "").strip()
        if not value:
            return None
        if not _EMAIL_OK.match(value):
            raise ValueError("Enter a valid email address.")
        return value

    @field_validator("username")
    @classmethod
    def clean_username(cls, value):
        value = (value or "").strip()
        if not value:
            return None
        if any(ord(ch) < 32 for ch in value):
            raise ValueError("Username contains invalid characters.")
        return value

    @field_validator("profile_url")
    @classmethod
    def safe_url(cls, value):
        value = (value or "").strip()
        if not value:
            return None
        parsed = urlparse(value)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("Profile URL must start with http:// or https://")
        if parsed.username or parsed.password:
            raise ValueError("Profile URL must not contain a username or password.")
        return value
