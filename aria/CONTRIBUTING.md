# Contributing to Aria

## Branch Strategy

- `main` — protected; only merged via PR after Claude APPROVED verdict
- `phase-{N}/{agent-name}` — one branch per agent per phase

## Commit Format

Conventional Commits, scoped to the agent's domain:

```
feat(scaffold): initialize FastAPI app with health endpoint
feat(auth): add JWT refresh token rotation
fix(pipeline): correct embedding shape (1,T) not (1,1,T)
test(qa): add GDPR cascade test for account deletion
chore(devops): add Fly.io fly.toml
```

Scopes: `scaffold`, `auth`, `pipeline`, `conversation`, `analysis`, `flashcards`, `frontend`, `devops`, `qa`, `cloud`

## Code Standards

**Python**:
- Type annotations on all functions (PEP 484)
- Full docstrings on all public functions (Args, Returns/Yields, Raises, Note)
- Ruff for linting + formatting (replaces Black + isort + flake8)
- No cross-module imports (see ADR-010)
- No hardcoded API keys, URLs, or model names — all in `core/config.py`

**TypeScript**:
- Strict mode enabled
- JSDoc on all exported components and hooks
- No `any` types

## Future-Proofing Checklist (Quinn_QA verifies at every gate)

- [ ] Every new external service has an abstract interface in `services/interfaces.py`
- [ ] Every new feature has a feature flag in `core/config.py`
- [ ] Every architectural decision has an ADR in `docs/adr/`
- [ ] Every API endpoint has summary + description + response codes
- [ ] Every Python function has a full docstring
- [ ] Every exported TypeScript component/hook has a JSDoc block
- [ ] Every new env var is added to `.env.example` with an inline comment
- [ ] Every new module has a `README.md`
- [ ] `CHANGELOG.md` updated
- [ ] No cross-module imports
- [ ] No hardcoded credentials

## Gate Process

1. Agent completes phase work
2. Agent runs pytest + vitest → must be 0 failures
3. Agent runs audio tests (if applicable phase)
4. Agent writes `aria/.claude/gates/gate-{N}.md`
5. Agent updates `aria/CLAUDE.md`
6. Agent opens PR from `phase-{N}/{agent}` → `main`
7. Claude reads gate report cold and issues APPROVED / BLOCKED
8. If APPROVED: squash-merge, tag `gate-{N}-approved`, cut next branch
