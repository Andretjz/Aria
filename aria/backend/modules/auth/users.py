"""FastAPI-Users infrastructure — UserManager, auth backend, current_user dependency."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, CookieTransport, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from aria.backend.core.config import settings
from aria.backend.database import get_db
from aria.backend.modules.auth.models import OAuthAccount, User, UserPreferences


async def get_user_db(session: AsyncSession = Depends(get_db)):
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)


# ── Cookie transport (HttpOnly, Secure in prod) ────────────────────────────

cookie_transport = CookieTransport(
    cookie_name="aria_access",
    cookie_max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    cookie_httponly=True,
    cookie_secure=not settings.DEBUG,
    cookie_samesite="lax",
)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.SECRET_KEY,
        lifetime_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


auth_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)


# ── UserManager ────────────────────────────────────────────────────────────

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def on_after_register(self, user: User, request: Optional[object] = None) -> None:
        """Create default UserPreferences when a new account is registered."""
        prefs = UserPreferences(user_id=user.id)
        self.user_db.session.add(prefs)
        await self.user_db.session.commit()


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


# ── FastAPIUsers instance ──────────────────────────────────────────────────

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
current_user_optional = fastapi_users.current_user(optional=True)
