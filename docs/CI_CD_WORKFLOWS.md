# GitHub Actions CI/CD Workflows Documentation

## Overview

This document describes the comprehensive CI/CD pipeline configured for KeneyApp using GitHub Actions. The pipeline includes linting, formatting, testing, security scanning, and deployment workflows.

---

## Workflow Files

### 1. `comprehensive-ci.yml` - Main CI Pipeline

**Trigger**: Push to `main`/`develop`, Pull Requests
**Purpose**: Continuous Integration with comprehensive testing and validation

#### Jobs (in order):

1. **quick-checks** (15 min)
   - Flake8 linting (Python)
   - Black format checking
   - isort import checking
   - ESLint (Frontend)
   - Prettier format checking (Frontend)
   - **Fails fast** if style violations found

2. **backend-test** (30 min)
   - Matrix: Python 3.11, 3.12, 3.13
   - Unit tests
   - Code coverage (Python 3.13 only)
   - Database migrations
   - Uploads coverage to Codecov
   - Uploads test results as artifacts

3. **frontend-test** (20 min)
   - Matrix: Node 18, 20, 22
   - Runs linter
   - Runs tests with coverage
   - Builds frontend
   - Uploads build artifacts

4. **type-checking** (15 min, non-blocking)
   - mypy type checking
   - Reports issues but doesn't fail build

5. **security-check** (20 min)
   - Bandit security scanning
   - Safety dependency checking
   - pip-audit vulnerability scanning
   - OWASP Dependency-Check
   - Uploads all reports as artifacts

6. **integration-test** (45 min)
   - Full application startup
   - Database initialization
   - E2E integration tests
   - Frontend build integration
   - E2E test screenshots/results

7. **performance** (20 min, non-blocking)
   - Performance benchmarks
   - Generates HTML report
   - Uploads benchmark artifacts

8. **docs-validation** (10 min, non-blocking)
   - Markdown file validation
   - Broken link checking
   - API documentation presence

9. **build-and-deploy** (30 min)
   - **Only runs on**: `main` branch push
   - Builds Docker image
   - Pushes to Container Registry (ghcr.io)
   - Deploys to staging environment

10. **final-status** (5 min)
    - Checks all critical jobs passed
    - Slack notification on failure
    - PR comment with results

---

### 2. `push-validation.yml` - Push Validation

**Trigger**: Push to `main`/`develop` (non-doc files)
**Purpose**: Quick validation on every push

#### Jobs:

1. **validate-push**
   - Commit message format validation (Conventional Commits)
   - Python syntax checking
   - Alerts on critical file changes

2. **dependabot** (if applicable)
   - Auto-approves patch updates
   - Auto-merges dependency updates

---

### 3. `deploy.yml` - Staging & Production Deployment

**Trigger**: 
- Push to `main` (staging only)
- Tags matching `v*.*.*` (production)
- Manual workflow dispatch

#### Jobs:

1. **build** (30 min)
   - Builds Docker image with multi-stage
   - Pushes to ghcr.io
   - Tags with: branch, semver, sha, latest

2. **scan** (15 min, non-blocking)
   - Trivy vulnerability scanning
   - Uploads results to GitHub Security tab
   - Reports critical/high severity issues

3. **deploy-staging** (30 min)
   - **Triggered**: Main branch push
   - SSH to staging server
   - Pulls latest image
   - Runs migrations
   - Smoke tests
   - Slack notification

4. **approval**
   - **Triggered**: Version tag push
   - Waits for manual environment approval

5. **deploy-production** (45 min)
   - **Triggered**: Version tag push + approval
   - Database backup
   - Blue-green deployment
   - Migration execution
   - Smoke tests
   - Slack notification
   - Release notes generation

---

## Configuration & Secrets

### Required GitHub Secrets

**Staging Deployment**:
- `STAGING_DEPLOY_KEY` - SSH private key (base64 encoded)
- `STAGING_HOST` - Server hostname
- `STAGING_USER` - SSH user

**Production Deployment**:
- `PRODUCTION_DEPLOY_KEY` - SSH private key (base64 encoded)
- `PRODUCTION_HOST` - Server hostname
- `PRODUCTION_USER` - SSH user

**Notifications**:
- `SLACK_WEBHOOK` - Slack webhook URL for notifications

### Environment Variables

**Auto-detected**:
- `PYTHON_VERSION` = "3.13"
- `NODE_VERSION` = "20"
- `REGISTRY` = "ghcr.io"

---

## Branch Protection Rules (Recommended)

### For `main` branch:

1. **Require status checks to pass before merging**:
   - `quick-checks`
   - `backend-test (Python 3.13)`
   - `frontend-test (Node 20)`
   - `security-check`
   - `integration-test`

2. **Require branches to be up to date before merging**: ✅

3. **Require code reviews before merging**: 1 approval

4. **Require conversation resolution before merging**: ✅

5. **Require signed commits**: ✅ (recommended for security)

6. **Require status checks from other services**: Only if applicable

---

## Running Workflows Manually

### Via GitHub UI:

1. Go to **Actions** tab
2. Select workflow (e.g., "Comprehensive CI Pipeline")
3. Click **Run workflow**
4. Select branch/options
5. Click green **Run workflow** button

### Via GitHub CLI:

```bash
# Trigger comprehensive CI
gh workflow run comprehensive-ci.yml -r main

# Trigger deployment
gh workflow run deploy.yml -r main -f environment=staging

# View workflow runs
gh run list --workflow=comprehensive-ci.yml

# View detailed results
gh run view <RUN_ID>
```

---

## Performance & Optimization

### Caching Strategy:

1. **pip cache** - Python dependencies
   - Key: `setup.py-${{ hashFiles('requirements.txt') }}`
   - Saves ~2 minutes per run

2. **npm cache** - Node dependencies
   - Key: `node-${{ hashFiles('frontend/package-lock.json') }}`
   - Saves ~1 minute per run

3. **Docker cache** - Build layers
   - type=gha (GitHub Actions cache backend)
   - Saves ~10 minutes on image build

### Matrix Strategy Benefits:

- **Backend**: Tests across Python 3.11/3.12/3.13 (parallel)
- **Frontend**: Tests across Node 18/20/22 (parallel)
- ~30% faster with parallel matrix jobs

### Concurrency Control:

- `concurrency` group cancels previous runs on new push
- Prevents resource waste from duplicate runs
- Useful for rapid iteration

---

## Security Considerations

### 1. Secret Management

- Secrets use base64 encoding
- Never logged or printed
- GitHub automatically masks in logs
- Use separate secrets for staging/production

### 2. OIDC Token Authentication (Recommended)

```yaml
# Instead of raw secrets, use OIDC for AWS/Azure/GCP
permissions:
  id-token: write
  contents: read
```

### 3. Minimal Permissions

- Only request needed permissions
- Use `permissions` block to limit scope
- Example: `contents: read` (not `write`)

### 4. Vulnerability Scanning

- Trivy scans Docker images
- pip-audit scans Python packages
- Bandit scans Python code
- Safety checks dependencies

---

## Monitoring & Observability

### Slack Notifications

- Sent on CI failure
- Includes commit/author info
- Links to workflow results
- Customize in `final-status` job

### PR Comments

- Auto-comments with test results
- Shows coverage changes
- Performance comparisons
- Only on PRs

### Artifact Retention

- Coverage reports: 5 days
- Test results: 5 days
- Security reports: 30 days
- E2E artifacts: 5 days
- Benchmark results: 5 days

---

## Troubleshooting

### Workflow Fails to Start

**Cause**: Branch protection requires passing checks
**Solution**: 
1. Ensure all required jobs pass
2. Check secret configurations
3. Verify branch protection rules

### Tests Pass Locally But Fail in CI

**Possible Issues**:
1. Different Python/Node versions
2. Missing environment variables
3. Database/Redis connectivity
4. File path differences (Windows vs Linux)

**Debug Steps**:
```bash
# SSH into runner
gh run view <RUN_ID> --log

# Run locally in Docker
docker-compose -f docker-compose.ci.yml up

# Test specific environment
python -m pytest tests/ -v --tb=short
```

### Deployment Hangs

**Symptoms**: Deploy job stuck at "waiting for health"
**Solutions**:
1. Check server SSH connectivity
2. Verify image pull successful
3. Check Docker daemon running
4. Review server logs

### Out of Disk Space

**Cause**: Multiple job artifacts accumulate
**Solution**: 
1. Reduce artifact retention (default: 5 days)
2. Clear old runners
3. Use GitHub's cache cleanup

---

## Best Practices

### 1. Keep Workflows Focused

Each workflow should have a single responsibility:
- `comprehensive-ci.yml` → Testing
- `push-validation.yml` → Fast checks
- `deploy.yml` → Deployment

### 2. Fail Fast

Quick checks first:
1. Linting (seconds)
2. Format checking (seconds)
3. Unit tests (minutes)
4. Integration tests (slower)

### 3. Cache Aggressively

```yaml
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
    restore-keys: ${{ runner.os }}-pip-
```

### 4. Use Artifacts for Debugging

```yaml
- uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: debug-logs
    path: logs/
```

### 5. Parallel Jobs When Possible

```yaml
jobs:
  job1:
    runs-on: ubuntu-latest
  job2:
    runs-on: ubuntu-latest
  # Both run in parallel, not sequentially
```

---

## Sample GitHub CLI Commands

```bash
# List all workflows
gh workflow list

# List recent runs
gh run list

# View specific run
gh run view <RUN_ID> --log

# Cancel running workflow
gh run cancel <RUN_ID>

# Delete workflow run
gh run delete <RUN_ID>

# View job in run
gh run view <RUN_ID> --json jobs

# Download artifacts
gh run download <RUN_ID> -D artifacts/

# Re-run failed jobs
gh run rerun <RUN_ID> --failed
```

---

## Cost Optimization

### GitHub Actions Pricing (as of 2024)

- **Public repos**: FREE ✅
- **Private repos**: 
  - 2000 minutes/month free
  - Then $0.24/minute
  - Recommended: Set minute limits

### Cost Reduction Strategies

1. **Use matrix for parallel jobs** - Same cost, faster
2. **Cache dependencies** - Reduce download time
3. **Skip unnecessary jobs** - Use `if:` conditions
4. **Use smaller runners** - For simple tasks
5. **Merge workflows** - Avoid duplicate setup costs

### Estimated Monthly Cost (Private Repo)

- Comprehensive CI: ~500 minutes/month
- Deployments: ~100 minutes/month
- **Total**: ~600 minutes = FREE (under 2000 limit) ✅

---

## Maintenance & Updates

### Regular Checks

1. **Monthly**: Review action versions for updates
2. **Quarterly**: Review coverage/performance trends
3. **On-demand**: Update when requirements change

### Deprecation Handling

Old action versions get deprecated. Update with:

```bash
# Update action to latest version
gh api repos/{owner}/{repo}/actions/workflows \
  --jq '.workflows[].id' | while read id; do
  # Update workflow file with latest action versions
done
```

---

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Action](https://github.com/docker/build-push-action)
- [Trivy Vulnerability Scanner](https://github.com/aquasecurity/trivy-action)
- [codecov/codecov-action](https://github.com/codecov/codecov-action)
- [Slack GitHub Action](https://github.com/slackapi/slack-github-action)

---

## Contact & Support

For issues with CI/CD pipelines:
1. Check workflow logs: Actions → Workflow → Run
2. Review this documentation
3. Check GitHub Actions documentation
4. Open issue with full error logs

---

*Last updated: December 2024*
*Maintained by: DevOps Team*
