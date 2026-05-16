"""Auth module router — Phase 2 (Anna_Auth) full implementation.

Endpoints:
  POST /register          — create account (FastAPI-Users)
  POST /login             — email+password → HttpOnly JWT + refresh token cookie
  POST /logout            — revoke session, clear cookies
  POST /refresh           — rotate refresh token, issue new access token
  GET  /me                — current user profile + language preferences
  PATCH /me/preferences   — update language preferences
  GET  /me/export         — GDPR Article 20 data export
  DELETE /me              — GDPR Article 17 right to erasure
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi_users import exceptions as fu_exc
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from aria.backend.core.config import settings
from aria.backend.database import get_db
from aria.backend.modules.auth.models import OAuthAccount, UserPreferences, UserSession
from aria.backend.modules.auth.schemas import (
    GDPRExport,
    LoginRequest,
    UserCreate,
    UserPreferencesRead,
    UserPreferencesUpdate,
    UserRead,
    UserWithPreferencesRead,
)
from aria.backend.modules.auth.users import (
    auth_backend,
    current_active_user,
    fastapi_users,
    get_jwt_strategy,
    get_user_manager,
)

router = APIRouter()

# ── Registration (FastAPI-Users handles hashing + validation) ──────────────

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
)


# ── Cookie helpers ─────────────────────────────────────────────────────────

def _set_access_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="aria_access",
        value=token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
    )


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="aria_refresh",
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        path="/api/v1/auth",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("aria_access", samesite="lax")
    response.delete_cookie("aria_refresh", path="/api/v1/auth", samesite="lax")


# ── Login ──────────────────────────────────────────────────────────────────

@router.post("/login", response_model=UserWithPreferencesRead, status_code=status.HTTP_200_OK)
async def login(
    request: Request,
    response: Response,
    credentials: LoginRequest,
    user_manager=Depends(get_user_manager),
    db: AsyncSession = Depends(get_db),
) -> UserWithPreferencesRead:
    try:
        user = await user_manager.get_by_email(credentials.email)
    except fu_exc.UserNotExists:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    verified, _ = user_manager.password_helper.verify_and_update(
        credentials.password, user.hashed_password
    )
    if not verified:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account is disabled")

    # Issue access token via FastAPI-Users JWTStrategy (ensures correct JWT format)
    strategy = get_jwt_strategy()
    access_token = await strategy.write_token(user)
    _set_access_cookie(response, access_token)

    # Create refresh token session
    raw_refresh, token_hash = UserSession.make_token()
    session = UserSession(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    db.add(session)
    await db.commit()
    _set_refresh_cookie(response, raw_refresh)

    # Fetch preferences (separate query — user object comes from a different session)
    prefs_result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == user.id)
    )
    prefs = prefs_result.scalar_one_or_none()

    return UserWithPreferencesRead(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_verified=user.is_verified,
        preferences=UserPreferencesRead.model_validate(prefs) if prefs else None,
    )


# ── Logout ─────────────────────────────────────────────────────────────────

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    user=Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    raw_refresh = request.cookies.get("aria_refresh")
    if raw_refresh:
        import hashlib
        token_hash = hashlib.sha256(raw_refresh.encode()).hexdigest()
        result = await db.execute(
            select(UserSession).where(UserSession.token_hash == token_hash)
        )
        session = result.scalar_one_or_none()
        if session and not session.is_revoked:
            session.is_revoked = True
            await db.commit()
    _clear_auth_cookies(response)


# ── Refresh ────────────────────────────────────────────────────────────────

@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_token(
    request: Request,
    response: Response,
    user_manager=Depends(get_user_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    raw_refresh = request.cookies.get("aria_refresh")
    if not raw_refresh:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing refresh token")

    import hashlib
    token_hash = hashlib.sha256(raw_refresh.encode()).hexdigest()
    result = await db.execute(
        select(UserSession).where(UserSession.token_hash == token_hash)
    )
    session = result.scalar_one_or_none()

    if not session or session.is_revoked:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    if session.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token expired")

    try:
        user = await user_manager.get(session.user_id)
    except fu_exc.UserNotExists:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    if not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account is disabled")

    # Rotate: revoke old session, create new one
    session.is_revoked = True
    raw_new, new_hash = UserSession.make_token()
    new_session = UserSession(
        user_id=user.id,
        token_hash=new_hash,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    db.add(new_session)
    await db.commit()

    strategy = get_jwt_strategy()
    access_token = await strategy.write_token(user)
    _set_access_cookie(response, access_token)
    _set_refresh_cookie(response, raw_new)

    return {"detail": "Token refreshed"}


# ── /me endpoints ──────────────────────────────────────────────────────────

@router.get("/me", response_model=UserWithPreferencesRead)
async def get_me(
    user=Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserWithPreferencesRead:
    prefs_result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == user.id)
    )
    prefs = prefs_result.scalar_one_or_none()
    return UserWithPreferencesRead(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_verified=user.is_verified,
        preferences=UserPreferencesRead.model_validate(prefs) if prefs else None,
    )


@router.patch("/me/preferences", response_model=UserPreferencesRead)
async def update_preferences(
    updates: UserPreferencesUpdate,
    user=Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserPreferencesRead:
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == user.id)
    )
    prefs = result.scalar_one_or_none()
    if prefs is None:
        prefs = UserPreferences(user_id=user.id)
        db.add(prefs)

    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(prefs, field, value)

    await db.commit()
    await db.refresh(prefs)
    return UserPreferencesRead.model_validate(prefs)


# ── GDPR ───────────────────────────────────────────────────────────────────

@router.get(
    "/me/export",
    response_model=GDPRExport,
    summary="GDPR Article 20 — right to data portability",
)
async def export_data(
    user=Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GDPRExport:
    prefs_result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == user.id)
    )
    prefs = prefs_result.scalar_one_or_none()

    sessions_result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.is_revoked.is_(False),
        )
    )
    active_sessions = sessions_result.scalars().all()

    oauth_result = await db.execute(
        select(OAuthAccount).where(OAuthAccount.user_id == user.id)
    )
    oauth_accounts = oauth_result.scalars().all()

    return GDPRExport(
        exported_at=datetime.now(timezone.utc),
        user={
            "id": str(user.id),
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
        },
        preferences={
            "input_lang": prefs.input_lang,
            "target_lang": prefs.target_lang,
            "feedback_lang": prefs.feedback_lang,
            "ui_lang": prefs.ui_lang,
        }
        if prefs
        else None,
        sessions_count=len(active_sessions),
        oauth_providers=[acc.oauth_name for acc in oauth_accounts],
    )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="GDPR Article 17 — right to erasure",
)
async def delete_account(
    response: Response,
    user=Depends(current_active_user),
    user_manager=Depends(get_user_manager),
) -> None:
    await user_manager.delete(user)
    _clear_auth_cookies(response)
