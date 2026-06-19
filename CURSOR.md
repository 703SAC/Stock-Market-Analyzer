# Cursor Guidelines for This Repo

This repository includes a committed Cursor project rule at `.cursor/rules/karpathy-guidelines.mdc`.

## Usage

1. Open this repository in Cursor.
2. Ensure project rules are enabled.
3. Confirm `karpathy-guidelines` appears in project rules.

## What this rule enforces

- Clarify assumptions before coding.
- Prefer simple implementations.
- Keep changes surgical and local.
- Use verifiable success criteria and checks.

## Project-specific guardrails

- `open-trading-api` is read-only unless explicitly requested otherwise.
- `kis-ai-extensions` is development tooling/reference, not runtime dependency.
- Keep adapter boundaries and avoid leaking secrets.