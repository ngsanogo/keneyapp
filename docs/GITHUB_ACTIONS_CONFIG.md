# GitHub Actions Configuration Guide

This file documents the GitHub Actions CI/CD setup for KeneyApp.

## Installed Actions & Versions

### Core Actions
- `actions/checkout@v4` - Check out code
- `actions/setup-python@v4` - Python setup with caching
- `actions/setup-node@v4` - Node.js setup with caching
- `actions/cache@v3` - Generic caching
- `actions/upload-artifact@v4` - Upload build artifacts
- `actions/download-artifact@v4` - Download artifacts
- `actions/github-script@v7` - Run JavaScript with GitHub API

### Code Quality & Linting
- `docker/setup-buildx-action@v3` - Docker buildx
- `docker/login-action@v3` - Docker registry login
- `docker/build-push-action@v5` - Build & push Docker images
- `docker/metadata-action@v5` - Generate Docker metadata

### Security & Scanning
- `aquasecurity/trivy-action@master` - Trivy vulnerability scanning
- `github/codeql-action/upload-sarif@v2` - Upload security results
- `dependabot/fetch-metadata@v1` - Dependabot metadata

### Notifications
- `slackapi/slack-github-action@v1.24.0` - Slack notifications

### Coverage
- `codecov/codecov-action@v3` - Codecov integration

## Tool Versions in Use

### Python Ecosystem
- Python: 3.11, 3.12, 3.13
- pytest: Latest (from requirements-test.txt)
- flake8: Latest (from requirements-dev.txt)
- black: Latest (from requirements-dev.txt)
- mypy: Latest (from requirements-dev.txt)
- bandit: Latest (installed in workflow)
- safety: Latest (installed in workflow)
- pip-audit: Latest (installed in workflow)

### Node.js Ecosystem
- Node.js: 18, 20, 22
- npm: Comes with Node.js
- ESLint: Configured in frontend/package.json
- Prettier: Configured in frontend/package.json

### Database & Services
- PostgreSQL: 15-alpine (Docker)
- Redis: 7-alpine (Docker)
- Docker: Latest on ubuntu-latest

## Environment Setup

### Python Environment
```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.13'
    cache: 'pip'
```

**Cache behavior**:
- Automatically caches `~/.cache/pip`
- Key based on: `setup.py`, `requirements.txt`, `pyproject.toml`
- Restore keys for partial matches

### Node Environment
```yaml
- name: Set up Node
  uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: 'npm'
    cache-dependency-path: 'frontend/package-lock.json'
```

**Cache behavior**:
- Automatically caches `~/.npm`
- Key based on: `package-lock.json`

## Service Configuration

### PostgreSQL
```yaml
services:
  postgres:
    image: postgres:15-alpine
    env:
      POSTGRES_USER: keneyapp
      POSTGRES_PASSWORD: keneyapp_secure_pass
      POSTGRES_DB: keneyapp_test
```

### Redis
```yaml
services:
  redis:
    image: redis:7-alpine
```

## Workflow Triggers

### Comprehensive CI
```yaml
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  workflow_dispatch:
```

### Push Validation
```yaml
on:
  push:
    branches: [ main, develop ]
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

### Deploy
```yaml
on:
  push:
    branches: [ main ]
    tags: [ 'v*.*.*' ]
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [ staging, production ]
```

## Concurrency & Resource Management

### Concurrency Settings
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

**Behavior**:
- Only one workflow run per ref (branch/tag)
- Previous runs cancelled on new push
- Prevents resource waste

### Timeout Management
- Quick checks: 15 minutes
- Unit tests: 30 minutes
- Frontend tests: 20 minutes
- Integration tests: 45 minutes
- Full deployment: 45 minutes

## Artifact Management

### Upload Configuration
```yaml
- uses: actions/upload-artifact@v4
  with:
    name: coverage-report
    path: htmlcov/
    retention-days: 5
```

**Retention Policies**:
- Coverage reports: 5 days
- Test results: 5 days
- Security reports: 30 days
- Build artifacts: 1 day
- E2E results: 5 days

**Storage costs**: ~$0.50/GB/month

## Docker Configuration

### Multi-Stage Building
```dockerfile
# Uses cache mount for faster builds
# Separates build and runtime stages
# Reduces final image size
```

### Registry
- GitHub Container Registry (ghcr.io)
- Authentication: GITHUB_TOKEN
- Tags: branch, semver, sha, latest

## Security Practices

### Secrets Management
- Never echo secrets in logs
- Use base64 encoding for SSH keys
- Limit secret scope to needed jobs
- Rotate regularly

### Permissions
```yaml
permissions:
  contents: read
  packages: write
  deployments: write
  id-token: write  # For OIDC
```

### Branch Protection
- Require status checks
- Require reviews
- Require conversation resolution
- Require up-to-date branches
- Require signed commits

## Matrix Strategy

### Backend Matrix
```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]
```

**Behavior**:
- Creates 3 parallel jobs
- One per Python version
- All must pass

### Frontend Matrix
```yaml
strategy:
  matrix:
    node-version: ["18", "20", "22"]
```

**Behavior**:
- Creates 3 parallel jobs
- One per Node version
- All must pass

## Cost Optimization

### Free Tier Limits
- 2000 free minutes/month (private repos)
- 20 concurrent jobs
- 35 days artifact retention

### Cost Reduction
1. Use matrix for parallel jobs (same cost, faster)
2. Skip non-critical jobs with `if:` conditions
3. Cache aggressively
4. Use smaller runners for simple tasks
5. Keep artifact retention short (5-7 days)

### Estimated Monthly Usage
- Comprehensive CI per push: ~5 minutes
- Tests per PR: ~10 minutes
- Deployments: ~15 minutes
- **Typical**: 300-500 minutes/month

## Troubleshooting

### Caching Issues
Problem: Cache not being restored
Solution:
1. Check cache key matches exactly
2. Verify `cache-dependency-path` correct
3. Clear cache in Actions settings
4. Re-run workflow

### Service Startup Failures
Problem: PostgreSQL/Redis doesn't start
Solution:
```yaml
- name: Wait for services
  run: |
    timeout 30 bash -c 'until pg_isready -h localhost -p 5432; do sleep 1; done'
```

### Matrix Job Failures
Problem: One matrix job fails, whole job fails
Solution: Use `continue-on-error: true` for non-critical
```yaml
- name: Run linter
  continue-on-error: true
```

### Secret Not Available in Job
Problem: Secret shows as `***` but not in env var
Solution:
1. Verify secret exists in repo settings
2. Check secret name matches exactly
3. Ensure job has correct permissions
4. Validate secret scope

## Maintenance

### Monthly Tasks
- Review action versions for updates
- Check for deprecation warnings
- Review workflow run times
- Verify all notifications working

### Quarterly Tasks
- Audit security report findings
- Review coverage trends
- Performance benchmarking
- Update documentation

### When Updating Actions
1. Check release notes for breaking changes
2. Test in non-critical branch first
3. Monitor first few runs carefully
4. Update all occurrences of action

## Additional Resources

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)
- [Action Validation](https://github.com/actions/setup-python#inputs)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)

## Contact

For CI/CD issues:
1. Check workflow logs
2. Review this documentation
3. Check GitHub Actions status
4. Open GitHub issue with logs
