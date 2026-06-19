# CLAUDE.md

Behavioral and project-context guidelines for coding agents in this repository.

Tradeoff: These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## Project Context (Stock-Market-Analyzer)

- Primary app code lives under `app/backend` (FastAPI) and `app/frontend` (Next.js).
- `open-trading-api` is an external sample/code source. Treat it as read-only unless explicitly requested.
- Do not add runtime imports from `kis-ai-extensions` into backend/frontend application logic. Use it as development/reference material only.
- Keep adapters and feature boundaries clear:
  - Router -> Feature service -> Adapter -> External API.
- Never expose secrets (`KIS`, `NAVER`, `OPENAI`, `GOOGLE`) in logs, responses, screenshots, or committed files.
- Respect KIS environment constraints:
  - `vps` does not support some prod-only endpoints (for example holiday checks).
  - Handle unsupported operations with explicit fallback behavior.

## 1. Think Before Coding

Do not assume. Surface uncertainty and tradeoffs before implementing.

Before implementation:
- State assumptions explicitly.
- If there are multiple interpretations, list options and ask.
- Push back if a simpler or safer approach exists.
- Stop and clarify if requirements conflict with project constraints.

Project-specific examples:
- If asked to "improve KIS data fetch", clarify whether this means `open-trading-api` changes (usually no) or adapter-layer changes in `app/backend/services/kis`.
- If asked for "trading-day precision", clarify whether prod holiday API access is available or a weekday fallback is required.

## 2. Simplicity First

Implement the minimum solution that satisfies today's requirement.

- No speculative features.
- No abstractions for one-off logic.
- No optional knobs/config unless requested.
- Prefer small, composable functions and existing project patterns.

Project-specific examples:
- For a screener filter, add the requested filter path only; do not introduce a full plugin strategy framework.
- For a report schema tweak, update the existing schema/validator instead of adding a second parallel report format.

## 3. Surgical Changes

Change only what is required for the task.

- Avoid drive-by refactors.
- Preserve local style and file layout.
- Do not reformat unrelated code.
- Remove only the dead code your own change creates.

Project-specific boundaries:
- Avoid touching `open-trading-api` unless explicitly requested.
- Keep frontend-only work inside `app/frontend` unless backend API changes are required.
- Keep backend-only work inside `app/backend` unless UI behavior must change.

## 4. Goal-Driven Execution

Use verifiable success criteria and iterate until checks pass.

Recommended loop:
1. Reproduce/define expected behavior (test or deterministic check).
2. Implement minimal change.
3. Verify with focused tests.
4. Re-run relevant existing tests to guard regressions.

Verification guidance for this repo:
- Backend: run targeted `pytest` for changed modules first.
- Frontend: run lint/typecheck/build checks relevant to changed files.
- API behavior changes: verify endpoint contract (status code + response shape) and error semantics.

## Working Agreement

- Prefer clear plans for multi-step tasks.
- Call out assumptions and unresolved risks in handoff notes.
- Keep diffs small and explain why each changed file is necessary.