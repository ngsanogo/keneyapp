# Coding Standards & Style Guides

This document defines the coding standards that keep KeneyApp code consistent, readable, and easy to maintain across backend, frontend, and infrastructure components.

## Guiding principles
- **Consistency first:** Prefer established patterns in the codebase over personal preference.
- **Automation over debate:** Let linters/formatters enforce style; avoid manual nitpicks during review.
- **Typed, documented code:** New and changed code should include type hints (or TypeScript types) and concise documentation where it improves clarity.
- **Small, testable units:** Keep functions/classes focused and covered by automated tests.

## Backend (Python)
- **Style guide:** [PEP 8](https://peps.python.org/pep-0008/) enforced via **Black** and **Flake8**.
- **Formatting:** `black app tests` (line length 88).
- **Linting:** `flake8 app tests` (configuration in `.flake8`).
- **Imports:** `isort --profile black app tests`.
- **Typing:** `mypy --config-file mypy.ini app` (strict on core modules; add annotations for new code).
- **Docstrings:** Use Google-style or reStructuredText docstrings for public functions/classes; explain *why* and *how* when behavior is non-obvious.

## Frontend (TypeScript/React)
- **Style guide:** Airbnb + React recommendations via ESLint (`frontend/.eslintrc`).
- **Formatting:** Prettier (`npm run format` / `npm run format:check`).
- **Linting:** `npm run lint` (runs ESLint with TypeScript rules).
- **Types:** Use strict typing (`unknown` > `any`), prefer discriminated unions and enums over string literals, and keep props/contexts typed.
- **Components:** Favor functional components and hooks; avoid side effects in render.

## Infrastructure & tooling
- **YAML:** Follow `.editorconfig`; keep keys sorted where practical and avoid tab characters.
- **Terraform:** Run `terraform fmt` before commits; keep modules small and parameterized.
- **Shell scripts:** Use `set -euo pipefail`; prefer long-form flags and quote variables.

## Naming conventions
- **Python:** `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- **TypeScript:** `camelCase` for functions/variables, `PascalCase` for components/types, `SCREAMING_SNAKE_CASE` for constants.
- **Files:** Python modules use `snake_case.py`; React components use `PascalCase.tsx`.
- **Branches & commits:** Follow the [Git & GitHub Best Practices](guides/GIT_GITHUB_BEST_PRACTICES.md) for branch names and Conventional Commits.

## Testing expectations
- Add/extend automated tests alongside feature or bugfix changes.
- Keep unit tests deterministic; isolate external effects with fixtures/mocks.
- Target >=80% coverage for new modules; explain gaps in PR descriptions when coverage drops.

## Enforcement
- **Pre-commit hooks:** Install and run `pre-commit run --all-files` before committing to apply formatting, linting, and secret scans.
- **Continuous Integration:** CI runs lint, format checks, type checks, and tests; failures must be resolved or justified before merge.
- **Code review:** Reviewers should block merges on style or testing regressions when automation signals issues.

## Quick commands
```bash
# Backend
black app tests && isort --profile black app tests && flake8 app tests && mypy --config-file mypy.ini app

# Frontend
(cd frontend && npm run format:check && npm run lint)

# Pre-commit across the repo
pre-commit run --all-files
```
