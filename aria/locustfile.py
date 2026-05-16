"""Aria load test — 10 concurrent users, p95 latency target < 5 s.

ADR-007 specifies: Fly.io machine spec (2 shared CPU / 4 GB RAM) must sustain
10 concurrent users with p95 response time below 5 s before Gate 8 approval.
If p95 > 5 s, upgrade to 4 shared CPU (~$30/month) before merge.

Run against production:
    locust -f aria/locustfile.py --host https://aria-backend.fly.dev \
           --users 10 --spawn-rate 2 --run-time 60s --headless

Run against local dev:
    locust -f aria/locustfile.py --host http://localhost:8000 \
           --users 10 --spawn-rate 2 --run-time 30s --headless
"""
from __future__ import annotations

import json
import random
import string

from locust import HttpUser, between, task


def _random_email() -> str:
    suffix = "".join(random.choices(string.ascii_lowercase, k=8))
    return f"load-{suffix}@test.aria"


class AriaUser(HttpUser):
    """Simulates a single authenticated Aria user hitting the main read endpoints."""

    wait_time = between(1, 3)

    def on_start(self) -> None:
        """Register + log in once per simulated user."""
        email = _random_email()
        password = "LoadTest!99"

        reg = self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
            name="/api/v1/auth/register",
        )
        if reg.status_code not in (200, 201, 400):
            reg.failure(f"Unexpected register status: {reg.status_code}")
            return

        login = self.client.post(
            "/api/v1/auth/login",
            json={"username": email, "password": password},
            name="/api/v1/auth/login",
        )
        if login.status_code not in (200, 204):
            login.failure(f"Login failed: {login.status_code}")

    @task(3)
    def health(self) -> None:
        self.client.get("/api/health", name="/api/health")

    @task(3)
    def get_me(self) -> None:
        self.client.get("/api/v1/auth/me", name="/api/v1/auth/me")

    @task(2)
    def flashcard_stats(self) -> None:
        self.client.get("/api/v1/flashcards/stats", name="/api/v1/flashcards/stats")

    @task(2)
    def due_cards(self) -> None:
        self.client.get("/api/v1/flashcards/due", name="/api/v1/flashcards/due")

    @task(1)
    def grammar_deficits(self) -> None:
        self.client.get("/api/v1/grammar/deficits", name="/api/v1/grammar/deficits")
