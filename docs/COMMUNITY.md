# Community & Collaboration Playbook

This guide explains how contributors, maintainers, and users can collaborate effectively on KeneyApp. Use it alongside the
[Contributing Guide](../CONTRIBUTING.md) and [Code of Conduct](../CODE_OF_CONDUCT.md) to keep interactions welcoming and
actionable.

## Participation Paths
- **Issues:** Report bugs, request features, or propose enhancements using the GitHub issue templates. Include steps to reproduce,
  expected/actual behavior, environment details, and screenshots/logs when relevant.
- **Pull requests:** Follow the branching strategy and Conventional Commits outlined in the Contributing Guide. Link PRs to their
  issues with `Fixes #<id>` and include tests or rationale for skipped coverage.
- **Discussions:** Use GitHub Discussions for Q&A, ideation, and sharing prototypes before opening an issue.
- **Docs improvements:** Suggest clarifications by opening `docs:` issues or PRs. Small copy edits are welcome via direct PRs.

## Issue Tracking & Triage
- **Labels:**
  - `type/bug`, `type/feature`, `type/chore` to classify work.
  - `priority/p0-p3` to communicate urgency.
  - `area/backend`, `area/frontend`, `area/docs`, `area/devops` for ownership.
  - `good first issue` and `help wanted` to highlight newcomer-friendly tasks.
- **Lifecycle:**
  1. **New:** Automatically labeled; maintainers validate scope and impact.
  2. **Triaged:** Labeled with type/area/priority and assigned or left open for community pickup.
  3. **In Progress:** Linked to a branch/PR; status updated weekly.
  4. **In Review:** Active PR linked; reviewers added per code ownership.
  5. **Done/Closed:** Merged, released, or declined with rationale documented.
- **Cadence:** Maintainers run triage **twice weekly** and respond to new issues within **48 business hours**. Security issues follow
  the private process in [SECURITY.md](../SECURITY.md).

## Community Engagement
- **Office hours:** A monthly community call (announced in Discussions) for roadmap updates, demos, and Q&A.
- **Working groups:** Ad-hoc groups for themes (observability, access control, UX). Join via Discussions; decisions and action items
  are tracked in linked issues.
- **Recognition:** Frequent contributors are highlighted in release notes; exceptional efforts may receive maintainer invitations.
- **Respect & inclusivity:** All interactions must follow the Code of Conduct. Disagreements should focus on the work, not people.

## Pull Request Collaboration
- **Proposal first:** For large changes, open a Discussion or draft PR to validate scope before implementation.
- **Checklists:** Include testing evidence, screenshots for UI changes, and rollout notes if behavior changes.
- **Review etiquette:**
  - Authors: keep PRs small and focused; respond to feedback promptly.
  - Reviewers: be constructive and specific; prefer suggestion mode for minor edits.
- **Merge policy:** Two approvals required for riskier areas (auth, data model, infra); one approval for low-risk docs or UI copy
  changes when tests pass.

## Roadmap & Feedback
- **Roadmap requests:** Open a `type/feature` issue with a problem statement, users impacted, and success metrics.
- **Feedback loop:** Share usability notes in Discussions; we collect themes for quarterly planning.
- **Transparency:** Significant roadmap shifts are summarized in release notes and pinned Discussions so contributors stay aligned.
