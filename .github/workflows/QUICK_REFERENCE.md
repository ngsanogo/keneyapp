name: Quick Reference - CI/CD Pipeline

on:
  workflow_dispatch:

# This file serves as documentation - not an actual workflow

# ============================================================================
# WORKFLOW OVERVIEW
# ============================================================================

## Available Workflows

1. **comprehensive-ci.yml**
   - Triggers: Push to main/develop, Pull requests
   - Duration: ~2 hours
   - Purpose: Complete CI testing & validation
   - Status: Required ✅

2. **push-validation.yml**
   - Triggers: Push to main/develop (non-docs)
   - Duration: ~5 minutes
   - Purpose: Quick syntax & format checks
   - Status: Optional ℹ️

3. **deploy.yml**
   - Triggers: Push to main (staging), Tag v*.*.* (production)
   - Duration: ~1 hour
   - Purpose: Automated deployment
   - Status: Conditional 🚀

# ============================================================================
# JOB TIMING & DEPENDENCIES
# ============================================================================

Comprehensive CI Pipeline:
├── quick-checks (15 min)               ← Fails fast on style issues
├── backend-test (30 min, Python 3x3)   ← Parallel matrix
├── frontend-test (20 min, Node 3x3)    ← Parallel matrix
├── type-checking (15 min)              ← Non-blocking
├── security-check (20 min)             ← Artifact upload
├── integration-test (45 min)           ← After unit tests
├── performance (20 min)                ← Non-blocking
├── docs-validation (10 min)            ← Non-blocking
├── build-and-deploy (30 min)           ← After all tests pass
└── final-status (5 min)                ← Last job

# ============================================================================
# REQUIRED STATUS CHECKS FOR MAIN
# ============================================================================

✅ BLOCKING (must pass):
  - quick-checks
  - backend-test (Python 3.13)
  - frontend-test (Node 20)
  - security-check
  - integration-test
  - final-status

⚠️ NON-BLOCKING (informational):
  - type-checking
  - performance
  - docs-validation

# ============================================================================
# QUICK COMMANDS
# ============================================================================

## GitHub CLI

### View workflow status
gh workflow list
gh run list --workflow=comprehensive-ci.yml
gh run view <RUN_ID>

### Trigger manually
gh workflow run comprehensive-ci.yml -r main
gh workflow run deploy.yml -r main -f environment=staging

### Download artifacts
gh run download <RUN_ID> -D artifacts/

### Re-run failed jobs
gh run rerun <RUN_ID> --failed

## Git

### Push changes to trigger workflows
git push origin main

### Create tag to trigger production deploy
git tag -a v1.2.3 -m "Release 1.2.3"
git push origin v1.2.3

# ============================================================================
# EXPECTED BEHAVIOR
# ============================================================================

### On `git push origin main`:
1. Comprehensive CI starts (all jobs)
2. quick-checks runs first (15 min)
3. Other jobs run in parallel (30-45 min)
4. If all pass: build-and-deploy runs
5. Docker image pushed to ghcr.io
6. Automatically deployed to staging

### On Pull Request:
1. Comprehensive CI starts
2. Status checks show in PR
3. Must pass before merge allowed
4. PR comment with test results

### On Version Tag (v1.2.3):
1. Comprehensive CI runs (if not already done)
2. Docker image built with version tag
3. Deploy.yml triggers production deployment
4. Requires manual approval
5. Database backup created before deploy

# ============================================================================
# ENVIRONMENT VARIABLES (Auto-set)
# ============================================================================

REGISTRY: ghcr.io
PYTHON_VERSION: 3.13
NODE_VERSION: 20
IMAGE_NAME: github.repository

# ============================================================================
# SECRETS REQUIRED IN GITHUB
# ============================================================================

### For Staging Deployment:
- STAGING_DEPLOY_KEY (base64 SSH key)
- STAGING_HOST (server hostname)
- STAGING_USER (SSH username)

### For Production Deployment:
- PRODUCTION_DEPLOY_KEY (base64 SSH key)
- PRODUCTION_HOST (server hostname)
- PRODUCTION_USER (SSH username)

### For Notifications:
- SLACK_WEBHOOK (Slack webhook URL)

# ============================================================================
# ARTIFACT LOCATIONS
# ============================================================================

After workflow completes:
1. Go to Actions tab
2. Click on workflow run
3. Click "Artifacts" section
4. Download specific artifact

Available artifacts:
- coverage-report-backend (HTML)
- test-results-py3.x (XML)
- frontend-build-node18/20/22
- security-reports (JSON)
- benchmark-results (HTML)
- mypy-results (XML)
- e2e-results (screenshots/videos)

# ============================================================================
# TROUBLESHOOTING MATRIX
# ============================================================================

PROBLEM: Workflow fails at "quick-checks"
ACTION: 
  1. Run locally: `black --check --line-length=100 app tests`
  2. Run locally: `flake8 app tests`
  3. Fix issues
  4. Push again

PROBLEM: Database migration fails
ACTION:
  1. Check migration syntax: `alembic history`
  2. Verify migration exists in alembic/versions/
  3. Check for syntax errors in migration file
  4. Test locally: `alembic upgrade head`

PROBLEM: Security scan finds vulnerability
ACTION:
  1. Review artifact: security-reports.json
  2. Check vulnerability: bandit-report.json
  3. Update dependency: `pip install package==version`
  4. Re-run workflow

PROBLEM: Deployment hangs
ACTION:
  1. SSH to server: `ssh $DEPLOY_USER@$DEPLOY_HOST`
  2. Check Docker: `docker ps`
  3. Check logs: `docker logs keneyapp_app`
  4. Check disk space: `df -h`

PROBLEM: Tests pass locally, fail in CI
ACTION:
  1. Check Python version: `python --version`
  2. Check Node version: `node --version`
  3. Check environment variables
  4. Test with different Python versions locally

# ============================================================================
# COST MONITORING
# ============================================================================

Current Usage (estimated):
- Comprehensive CI: 5 min/push
- Per PR: 10 min/PR
- Per deployment: 15 min
- Typical: 300-500 min/month

Limits:
- Free tier: 2000 min/month
- Cost after: $0.24/min

Cost optimization:
✅ Using matrix (parallel, same cost)
✅ Caching dependencies
✅ Short artifact retention (5-7 days)
✅ Skip unnecessary jobs

# ============================================================================
# UPDATING WORKFLOWS
# ============================================================================

To modify workflows:
1. Edit file: .github/workflows/xxx.yml
2. Validate syntax (VS Code extension helps)
3. Commit changes
4. Push to main (triggers with new workflow)
5. Monitor first run carefully

To disable a workflow:
1. Add `enabled: false` to workflow file
2. Or: Disable in GitHub Actions settings

# ============================================================================
# BRANCH PROTECTION SETUP
# ============================================================================

Run this script to enable branch protection:
```bash
export GITHUB_TOKEN=<your-token>
bash scripts/setup-branch-protection.sh
```

This sets up:
✅ Require all status checks pass
✅ Require 1 review approval
✅ Require conversation resolution
✅ Require up-to-date before merge
✅ Enforce admins (bypasses checks)
✅ Prevent force push
✅ Prevent deletion

# ============================================================================
# NOTIFICATIONS
# ============================================================================

Currently configured:
- ✅ Slack notifications on failure
- ✅ PR comments with test results
- ✅ Deployment notifications

To enable more:
1. Configure Slack webhook in secrets
2. Add notification action to workflow
3. Test with manual trigger

# ============================================================================
# PERFORMANCE TIPS
# ============================================================================

Faster CI runs:
1. Squash related commits before push
2. Run linter locally before push
3. Keep branch up-to-date (reduces merge conflicts)
4. Avoid large commits

Faster local development:
1. Use `pytest -k <test>` for specific tests
2. Use `--cache` flag to skip slow tests
3. Run in Docker: `docker-compose up`

# ============================================================================
# USEFUL LINKS
# ============================================================================

- GitHub Actions Docs: https://docs.github.com/en/actions
- Actions Marketplace: https://github.com/marketplace?type=actions
- Workflow Syntax: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions
- Workflow Commands: https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions

# ============================================================================
# SUPPORT
# ============================================================================

For CI/CD issues:
1. Check workflow logs (Actions tab)
2. Review this documentation
3. Check GitHub Actions status page
4. Open GitHub issue with full logs

For deployment issues:
1. SSH to server
2. Check Docker logs
3. Check server resources
4. Check network connectivity

Contact: DevOps Team
Last updated: December 2024
