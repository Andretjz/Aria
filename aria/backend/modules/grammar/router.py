"""Grammar Workshop module router — Alice_Analysis (Phase 5).

GET /api/v1/grammar/deficits — aggregate grammar errors across all sessions.
"""
from __future__ import annotations

import json
from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aria.backend.database import get_db
from aria.backend.modules.analysis.models import AnalysisSession
from aria.backend.modules.grammar.schemas import GrammarDeficitRead

router = APIRouter()


@router.get(
    "/deficits",
    response_model=list[GrammarDeficitRead],
    summary="Get top grammar deficits",
    description=(
        "Returns the top-5 grammar rules with the most errors, "
        "aggregated across all analysis sessions. Ordered by total frequency."
    ),
)
async def get_deficits(
    db: AsyncSession = Depends(get_db),
) -> list[GrammarDeficitRead]:
    """Aggregate grammar spotlight data across all sessions and return top 5.

    Sessions without grammar data (pre-Phase-5 sessions or LLM failures)
    are skipped gracefully.

    Args:
        db: Injected database session.

    Returns:
        Up to 5 grammar deficits ordered by descending total frequency.
    """
    stmt = select(AnalysisSession.grammar_json).where(
        AnalysisSession.grammar_json.isnot(None)
    )
    rows = await db.execute(stmt)
    grammar_jsons = [row[0] for row in rows.fetchall()]

    aggregated: dict[str, dict] = defaultdict(
        lambda: {"rule": "", "total_frequency": 0, "example": None}
    )
    for raw in grammar_jsons:
        try:
            items = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            rule = str(item.get("rule", "")).strip()
            if not rule:
                continue
            freq = int(item.get("frequency", 1))
            aggregated[rule]["rule"] = rule
            aggregated[rule]["total_frequency"] += freq
            if aggregated[rule]["example"] is None and item.get("example"):
                aggregated[rule]["example"] = str(item["example"])

    top5 = sorted(
        aggregated.values(),
        key=lambda x: x["total_frequency"],
        reverse=True,
    )[:5]

    return [GrammarDeficitRead(**d) for d in top5]


@router.get(
    "/exercises/{rule_id}",
    summary="Get exercises for a grammar rule",
    description=(
        "Returns 3 progressive exercises for a specific grammar rule: "
        "explanation + audio example + fill-gap + auditive mini-test."
    ),
)
async def get_exercises(rule_id: str):
    return {"detail": "Not implemented — Phase 6"}
