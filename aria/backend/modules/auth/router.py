"""Auth module router — FastAPI-Users integration.

Full implementation by Anna_Auth in Phase 2.
Sam_Architect provides the skeleton so main.py can import without error.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.post(
    "/register",
    summary="Register a new account",
    description="Create a new Aria account with email + password. OAuth via /auth/google or /auth/github.",
    responses={
        201: {"description": "Account created"},
        400: {"description": "Email already registered"},
    },
)
async def register():
    """Register endpoint stub — implemented by Anna_Auth in Phase 2."""
    return {"detail": "Not implemented — Phase 2 (Anna_Auth)"}


@router.post(
    "/login",
    summary="Login with email + password",
    description="Returns JWT access token (15 min) as HttpOnly cookie + refresh token (7 days).",
)
async def login():
    """Login endpoint stub — implemented by Anna_Auth in Phase 2."""
    return {"detail": "Not implemented — Phase 2 (Anna_Auth)"}


@router.get(
    "/me",
    summary="Get current user",
    description="Returns the authenticated user's profile and language preferences.",
)
async def get_me():
    """Current user endpoint stub — implemented by Anna_Auth in Phase 2."""
    return {"detail": "Not implemented — Phase 2 (Anna_Auth)"}


@router.get(
    "/me/export",
    summary="GDPR data export",
    description=(
        "Returns a complete JSON export of all user data: profile, sessions, "
        "flashcards, grammar history. Required by GDPR Article 20."
    ),
)
async def export_data():
    """GDPR data export stub — implemented by Anna_Auth in Phase 6."""
    return {"detail": "Not implemented — Phase 6 (Anna_Auth)"}


@router.delete(
    "/me",
    summary="Delete account (GDPR right to erasure)",
    description=(
        "Permanently deletes the user and all associated data: sessions, flashcards, "
        "grammar history, audio files. Redis eviction within 1 hour. "
        "Required by GDPR Article 17."
    ),
)
async def delete_account():
    """Account deletion stub — implemented by Anna_Auth in Phase 6."""
    return {"detail": "Not implemented — Phase 6 (Anna_Auth)"}
