"""Auth Pydantic schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr


class UserPreferencesRead(BaseModel):
    input_lang: str
    target_lang: str
    feedback_lang: str
    ui_lang: str

    model_config = {"from_attributes": True}


class UserPreferencesUpdate(BaseModel):
    input_lang: str | None = None
    target_lang: str | None = None
    feedback_lang: str | None = None
    ui_lang: str | None = None


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserWithPreferencesRead(schemas.BaseUser[uuid.UUID]):
    preferences: UserPreferencesRead | None = None


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GDPRExport(BaseModel):
    exported_at: datetime
    user: dict[str, Any]
    preferences: dict[str, Any] | None
    sessions_count: int
    oauth_providers: list[str]
