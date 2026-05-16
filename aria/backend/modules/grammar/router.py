"""Grammar Workshop module router.

Full implementation by Alice_Analysis in Phase 5.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/deficits",
    summary="Get top grammar deficits",
    description=(
        "Returns the top-5 grammar rules the user makes errors on, "
        "aggregated across all sessions. Ordered by frequency."
    ),
)
async def get_deficits():
    return {"detail": "Not implemented — Phase 5 (Alice_Analysis)"}


@router.get(
    "/exercises/{rule_id}",
    summary="Get exercises for a grammar rule",
    description=(
        "Returns 3 progressive exercises for a specific grammar rule: "
        "explanation + audio example + fill-gap + auditive mini-test."
    ),
)
async def get_exercises(rule_id: str):
    return {"detail": "Not implemented — Phase 5 (Alice_Analysis)"}
