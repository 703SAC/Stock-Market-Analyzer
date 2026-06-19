---
name: karpathy-guidelines
description: Behavioral guidelines for coding agents in Stock-Market-Analyzer. Use to avoid hidden assumptions, overengineering, broad refactors, and unverifiable changes.
license: MIT
---

# Karpathy Guidelines (Stock-Market-Analyzer)

Behavioral rules adapted for this repository.

## Project context

- Main app code: `app/backend`, `app/frontend`.
- External sample source: `open-trading-api` (read-only by default).
- Development support only: `kis-ai-extensions` (do not import into runtime app paths).
- Preserve layered flow: Router -> Feature service -> Adapter -> External API.
- Keep secrets out of code, logs, and responses.

## 1. Think Before Coding

- State assumptions.
- Surface ambiguity and ask clarifying questions.
- Offer alternatives when multiple valid interpretations exist.
- Clarify constraint conflicts early (for example prod-only KIS endpoints vs vps environment).

## 2. Simplicity First

- Deliver the minimum implementation that solves the request.
- Avoid speculative flexibility and framework-like abstractions.
- Prefer extending existing feature/service schemas over creating parallel structures.

## 3. Surgical Changes

- Edit only what is necessary.
- Do not perform drive-by cleanup/refactoring.
- Match local style.
- Remove only artifacts created by your own change.

## 4. Goal-Driven Execution

- Turn tasks into measurable checks.
- For bugs: reproduce first, then fix, then verify.
- For features: define input/output contract and test that contract.

Suggested verification loop:
1. Define success criteria.
2. Implement minimal change.
3. Run targeted checks/tests.
4. Confirm no regressions in affected modules.