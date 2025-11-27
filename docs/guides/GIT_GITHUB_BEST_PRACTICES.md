# Git & GitHub Best Practices

These guidelines standardize how we branch, commit, and submit pull requests so changes stay traceable, reviewable, and ready for automation.

## Branching strategy
- **main**: Production-ready; only fast-forward or squash merges from validated integration branches.
- **develop**: Integration/staging; receives feature work after review and pre-release testing.
- **feature/***: New work items. Name with a short scope, e.g., `feature/patient-attachments`.
- **fix/* or hotfix/***: Urgent production fixes. Patch `main`, then forward-merge into `develop`.
- **chore/** and **docs/**: Maintenance or documentation-only branches to keep history searchable.

**Workflow**
1. Branch from `develop` for most work; branch from `main` only for hotfixes.
2. Keep branches short-lived and rebased on the latest target branch to reduce merge noise.
3. Prefer squash merges for feature branches to keep histories clean; use merge commits only when preserving context is necessary.
4. Delete merged branches on GitHub to avoid drift.

## Commit messages
- Use **Conventional Commits** (`type(scope): summary`). Common types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`, `build`.
- Limit the summary line to **72 characters**, using the imperative mood: `feat(api): add patient export endpoint`.
- Add a concise body when context or rationale matters; wrap lines at ~72 characters.
- Reference tickets in the footer with `Refs #123` or close them with `Closes #123`.
- Avoid mixing unrelated changes in a single commit; prefer small, reviewable units.

## Pull requests
- Target `develop` for new work and `main` only for release or hotfix flows.
- Keep PRs **scope-limited** (one theme) and **small enough to review** quickly.
- Include a clear description: what changed, why, and how it was tested. Link issues.
- Ensure **status checks pass** locally before opening the PR (tests, lint, type checks).
- Request at least **one review**; respond to feedback with follow-up commits (not force-pushes after review unless agreed).
- Mark breaking changes in the description and provide rollout/rollback notes when relevant.
- Use draft PRs for work in progress to share progress without triggering reviews.

## Pre-flight checklist
- [ ] Branch named using the conventions above and updated with the target branch.
- [ ] Commits follow Conventional Commits and group related changes logically.
- [ ] Tests/linting run locally; failing checks are explained or fixed.
- [ ] PR description includes scope, motivation, testing, and linked issues.
- [ ] No stray debug files or secrets; relevant documentation updated.
