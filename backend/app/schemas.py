from pydantic import BaseModel, Field, field_validator
from typing import Optional

class FootprintRequest(BaseModel):
    email: Optional[str] = Field(default=None, max_length=254)
    username: Optional[str] = Field(default=None, max_length=80)
    profile_url: Optional[str] = Field(default=None, max_length=500)

    @field_validator("email")
    @classmethod
    def clean_email(cls, value):
        if value:
            value = value.strip()
            if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
                raise ValueError("Enter a valid email address.")
        return value

    @field_validator("profile_url")
    @classmethod
    def safe_url(cls, value):
        if value:
            value = value.strip()
            if not value.startswith(("https://", "http://")):
                raise ValueError("Profile URL must start with http:// or https://")
        return value
