"""Phase 8 — Deployment configuration validation tests.

These tests assert that every config file required for the Fly.io + Vercel
deployment exists and contains the critical settings documented in ADR-007.
They run in CI without any network access or cloud credentials.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

# Resolve the aria/ monorepo root regardless of where pytest is invoked from.
ARIA_ROOT = Path(__file__).parents[2]   # aria/backend/tests/test_deployment.py → aria/
REPO_ROOT  = ARIA_ROOT.parent           # aria/ → repo root


# ── Production Dockerfile ─────────────────────────────────────────────────────

PROD_DOCKERFILE = ARIA_ROOT / "backend" / "Dockerfile"


def test_production_dockerfile_exists() -> None:
    assert PROD_DOCKERFILE.exists(), "aria/backend/Dockerfile (production) is missing"


def test_production_dockerfile_uses_slim_base() -> None:
    text = PROD_DOCKERFILE.read_text()
    assert "python:3.11-slim" in text, "Production image must use python:3.11-slim (no CUDA)"
    assert "nvidia/cuda" not in text, "Production image must not include CUDA layers"


def test_production_dockerfile_has_nonroot_user() -> None:
    text = PROD_DOCKERFILE.read_text()
    assert "USER aria" in text, "Production image must drop to non-root 'aria' user"


def test_production_dockerfile_exposes_8000() -> None:
    text = PROD_DOCKERFILE.read_text()
    assert "EXPOSE 8000" in text, "Production image must EXPOSE 8000"


def test_production_dockerfile_has_healthcheck() -> None:
    text = PROD_DOCKERFILE.read_text()
    assert "HEALTHCHECK" in text, "Production image must declare a HEALTHCHECK"
    assert "/api/health" in text, "HEALTHCHECK must target /api/health"


# ── fly.toml ─────────────────────────────────────────────────────────────────

FLY_TOML = ARIA_ROOT / "fly.toml"


def test_fly_toml_exists() -> None:
    assert FLY_TOML.exists(), "aria/fly.toml is missing"


def test_fly_toml_has_frankfurt_region() -> None:
    text = FLY_TOML.read_text()
    assert 'primary_region = "fra"' in text, (
        "Fly.io must deploy to Frankfurt (fra) for EU GDPR residency — see ADR-007"
    )


def test_fly_toml_has_correct_vm_memory() -> None:
    text = FLY_TOML.read_text()
    assert "memory_mb = 4096" in text, "Fly.io VM must be 4 GB RAM per ADR-007 spec"


def test_fly_toml_has_health_check_path() -> None:
    text = FLY_TOML.read_text()
    assert 'path         = "/api/health"' in text or 'path = "/api/health"' in text, (
        "fly.toml health check must target /api/health"
    )


def test_fly_toml_forces_https() -> None:
    text = FLY_TOML.read_text()
    assert "force_https" in text, "fly.toml must enforce HTTPS"


def test_fly_toml_has_backend_dockerfile_ref() -> None:
    text = FLY_TOML.read_text()
    assert "backend/Dockerfile" in text, "fly.toml must point to the production Dockerfile"


# ── vercel.json ───────────────────────────────────────────────────────────────

VERCEL_JSON = ARIA_ROOT / "frontend" / "vercel.json"


def test_vercel_json_exists() -> None:
    assert VERCEL_JSON.exists(), "aria/frontend/vercel.json is missing"


def test_vercel_json_is_valid_json() -> None:
    data = json.loads(VERCEL_JSON.read_text())
    assert isinstance(data, dict), "vercel.json must be a JSON object"


def test_vercel_json_has_api_proxy_rewrite() -> None:
    data = json.loads(VERCEL_JSON.read_text())
    rewrites = data.get("rewrites", [])
    api_rewrite = any(
        r.get("source", "").startswith("/api") and "fly.dev" in r.get("destination", "")
        for r in rewrites
    )
    assert api_rewrite, (
        "vercel.json must proxy /api/* to the Fly.io backend (credentials: include cookies)"
    )


def test_vercel_json_has_spa_fallback_rewrite() -> None:
    data = json.loads(VERCEL_JSON.read_text())
    rewrites = data.get("rewrites", [])
    spa_rewrite = any(
        r.get("destination") == "/index.html" for r in rewrites
    )
    assert spa_rewrite, (
        "vercel.json must rewrite all unmatched paths to /index.html for React SPA routing"
    )


# ── deploy.yml ────────────────────────────────────────────────────────────────

DEPLOY_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "deploy.yml"


def test_deploy_workflow_exists() -> None:
    assert DEPLOY_WORKFLOW.exists(), ".github/workflows/deploy.yml is missing"


def test_deploy_workflow_triggers_on_main() -> None:
    text = DEPLOY_WORKFLOW.read_text()
    assert "branches: [main]" in text, "deploy.yml must trigger only on pushes to main"


def test_deploy_workflow_has_fly_deploy_step() -> None:
    text = DEPLOY_WORKFLOW.read_text()
    assert "flyctl deploy" in text or "fly deploy" in text, (
        "deploy.yml must run flyctl deploy for the Fly.io backend"
    )


def test_deploy_workflow_has_smoke_test() -> None:
    text = DEPLOY_WORKFLOW.read_text()
    assert "/api/health" in text, (
        "deploy.yml must run a post-deploy smoke test against /api/health"
    )
