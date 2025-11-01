# Release Process

This document describes the release process for KeneyApp.

## Versioning

KeneyApp follows [Semantic Versioning (SemVer)](https://semver.org/):

**Format**: `MAJOR.MINOR.PATCH` (e.g., `2.1.3`)

- **MAJOR** version: Incompatible API changes or breaking changes
- **MINOR** version: New features or functionality (backwards compatible)
- **PATCH** version: Bug fixes and minor improvements (backwards compatible)

### Pre-release Versions

- **Alpha**: `v2.1.0-alpha.1` - Early testing, unstable
- **Beta**: `v2.1.0-beta.1` - Feature complete, testing phase
- **RC**: `v2.1.0-rc.1` - Release candidate, final testing

## Release Cycle

We follow a time-based release schedule:

- **Major releases**: Every 12-18 months
- **Minor releases**: Every 2-3 months
- **Patch releases**: As needed (usually weekly or bi-weekly)
- **Security releases**: Immediately when critical vulnerabilities are discovered

## Release Branch Strategy

We use **Git Flow** for managing releases:

```
main (production)
  ↑
  └── release/v2.1.0
        ↑
        └── develop (integration)
              ↑
              ├── feature/new-feature
              ├── bugfix/fix-issue
              └── ...
```

## Release Process Steps

### 1. Pre-Release Planning

**2 weeks before release:**

- [ ] Review and prioritize issues for the release
- [ ] Ensure all planned features are complete
- [ ] Update project roadmap
- [ ] Announce feature freeze in discussions

### 2. Feature Freeze

**1 week before release:**

- [ ] Stop merging new features to `develop`
- [ ] Focus on bug fixes and testing only
- [ ] Create release tracking issue
- [ ] Begin release documentation updates

### 3. Create Release Branch

```bash
# Ensure develop is up to date
git checkout develop
git pull origin develop

# Create release branch
git checkout -b release/v2.1.0

# Push release branch
git push origin release/v2.1.0
```

### 4. Prepare Release

**On the release branch:**

- [ ] Update version numbers:
  - `app/__init__.py` or `app/core/config.py`
  - `frontend/package.json`
  - `docker-compose.yml` (if needed)
  
- [ ] Update CHANGELOG.md:
  ```markdown
  ## [2.1.0] - 2025-11-15
  
  ### Added
  - New feature X
  - New feature Y
  
  ### Changed
  - Updated component Z
  
  ### Fixed
  - Bug fix A
  - Bug fix B
  
  ### Security
  - Security patch C
  ```

- [ ] Update documentation:
  - README.md (if needed)
  - API documentation
  - Deployment guides
  - Migration guides (for breaking changes)

- [ ] Run comprehensive tests:
  ```bash
  # Backend tests
  pytest --cov=app tests/
  
  # Frontend tests
  cd frontend && npm test
  
  # Integration tests
  docker-compose up -d
  pytest tests/test_smoke.py
  ```

- [ ] Security scan:
  ```bash
  # Python dependencies
  pip-audit
  
  # Frontend dependencies
  cd frontend && npm audit
  
  # Code scanning
  # (Runs automatically in CI)
  ```

### 5. Release Candidate Testing

- [ ] Deploy to staging environment
- [ ] Perform manual testing:
  - Authentication flows
  - Patient management
  - Appointment scheduling
  - Prescription handling
  - Dashboard functionality
  
- [ ] Load testing (for major releases):
  ```bash
  # Run performance tests
  pytest tests/test_performance.py
  ```

- [ ] Security testing
- [ ] Browser compatibility testing (frontend)

### 6. Bug Fixes

If bugs are found during testing:

```bash
# Fix on release branch
git checkout release/v2.1.0
# Make fixes...
git commit -m "fix: resolve issue with patient search"
git push origin release/v2.1.0

# Also merge to develop
git checkout develop
git merge release/v2.1.0
git push origin develop
```

### 7. Final Approval

**Release checklist:**

- [ ] All tests passing
- [ ] No critical/high severity bugs
- [ ] Documentation complete
- [ ] CHANGELOG.md updated
- [ ] Migration guide ready (if needed)
- [ ] Deployment plan reviewed
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured

### 8. Merge to Main

```bash
# Ensure all changes are committed
git checkout release/v2.1.0
git status

# Merge to main
git checkout main
git pull origin main
git merge --no-ff release/v2.1.0
git push origin main
```

### 9. Create Git Tag

```bash
# Create annotated tag
git tag -a v2.1.0 -m "Release version 2.1.0

Features:
- New feature X
- New feature Y

Improvements:
- Updated component Z

Bug Fixes:
- Fixed issue A
- Fixed issue B
"

# Push tag
git push origin v2.1.0
```

### 10. Create GitHub Release

1. Go to [Releases](https://github.com/ISData-consulting/keneyapp/releases)
2. Click "Draft a new release"
3. Select the tag (v2.1.0)
4. Fill in the release details:

```markdown
# KeneyApp v2.1.0

## 🎉 Highlights

Brief overview of major changes...

## ✨ New Features

- Feature 1 (#123)
- Feature 2 (#124)

## 🐛 Bug Fixes

- Fixed issue A (#125)
- Fixed issue B (#126)

## 📚 Documentation

- Updated deployment guide
- Added new API examples

## ⚠️ Breaking Changes

(If any)

## 🔄 Migration Guide

(If needed)

## 📦 Upgrade Instructions

### Docker Compose
\`\`\`bash
docker-compose pull
docker-compose up -d
\`\`\`

### Manual Deployment
\`\`\`bash
git pull origin main
git checkout v2.1.0
pip install -r requirements.txt
alembic upgrade head
\`\`\`

## 🙏 Contributors

Thanks to all contributors who made this release possible!

## 📝 Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete details.
```

5. Attach any release artifacts (if applicable)
6. Mark as pre-release (if alpha/beta/rc)
7. Publish release

### 11. Deploy to Production

Follow the [Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT_GUIDE.md):

```bash
# Pull latest changes
git pull origin main
git checkout v2.1.0

# Run migrations
alembic upgrade head

# Build and deploy
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
curl https://api.keneyapp.com/health
```

### 12. Merge Back to Develop

```bash
# Ensure develop includes all release fixes
git checkout develop
git merge main
git push origin develop
```

### 13. Clean Up

```bash
# Delete release branch (optional)
git branch -d release/v2.1.0
git push origin --delete release/v2.1.0
```

### 14. Post-Release

- [ ] Monitor application logs and metrics
- [ ] Check error tracking (Sentry, etc.)
- [ ] Verify all services are healthy
- [ ] Update release status in tracking issue
- [ ] Announce release:
  - GitHub Discussions
  - Social media (if applicable)
  - Email newsletter (if applicable)
- [ ] Close milestone (if used)
- [ ] Update project roadmap

## Hotfix Process

For critical bugs in production:

### 1. Create Hotfix Branch

```bash
# Branch from main (production)
git checkout main
git pull origin main
git checkout -b hotfix/v2.1.1
```

### 2. Fix the Issue

```bash
# Make the fix
git commit -m "fix: critical issue with authentication"
```

### 3. Test Thoroughly

- [ ] Write test to verify fix
- [ ] Run all tests
- [ ] Deploy to staging
- [ ] Manual verification

### 4. Update Version and Changelog

- Update version to v2.1.1
- Add to CHANGELOG.md

### 5. Merge to Main

```bash
git checkout main
git merge --no-ff hotfix/v2.1.1
git tag -a v2.1.1 -m "Hotfix: Critical authentication issue"
git push origin main
git push origin v2.1.1
```

### 6. Merge to Develop

```bash
git checkout develop
git merge hotfix/v2.1.1
git push origin develop
```

### 7. Deploy Immediately

Follow emergency deployment procedures.

## Rollback Process

If critical issues are discovered after release:

### Option 1: Quick Fix (Preferred)

1. Create hotfix branch from current production
2. Fix the issue
3. Follow hotfix process above

### Option 2: Rollback to Previous Version

```bash
# Identify last stable version
git tag --list

# Checkout previous version
git checkout v2.0.5

# Deploy previous version
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Rollback database if needed
alembic downgrade <previous_revision>
```

### Option 3: Forward Fix (Major Issues)

1. Revert problematic commits on main
2. Create new patch version
3. Deploy fixed version

## Version Support Policy

- **Current major version**: Fully supported
- **Previous major version**: Security updates only (12 months)
- **Older versions**: End of life, no updates

Example:
- v2.x.x: Fully supported
- v1.x.x: Security patches only
- v0.x.x: No longer supported

## Release Communication

### Internal Communication

- [ ] Notify development team
- [ ] Update internal documentation
- [ ] Brief operations team on changes

### External Communication

- [ ] GitHub Release notes
- [ ] CHANGELOG.md update
- [ ] Discussion post announcement
- [ ] Email to stakeholders (if applicable)

### Communication Template

```markdown
📢 KeneyApp v2.1.0 Released!

We're excited to announce the release of KeneyApp v2.1.0!

Key Highlights:
• New feature X
• Improved performance
• Bug fixes and improvements

Upgrade Instructions: [link]
Full Changelog: [link]

Thank you to all contributors!
```

## Troubleshooting

### Build Fails During Release

1. Check CI/CD logs
2. Verify all dependencies are up to date
3. Ensure database migrations are compatible
4. Test locally with clean environment

### Tests Fail on Release Branch

1. Identify failing tests
2. Fix on release branch
3. Merge fixes to develop
4. Re-run full test suite

### Database Migration Issues

1. Test migration on copy of production data
2. Have rollback plan ready
3. Consider data migration scripts
4. Document any manual steps needed

## Compliance and Auditing

For healthcare compliance (HIPAA/GDPR):

- [ ] Security audit completed
- [ ] Data privacy impact assessed
- [ ] Compliance documentation updated
- [ ] Audit logs verified
- [ ] Access controls reviewed

## Emergency Release Process

For critical security issues:

1. **Immediate**: Assess severity and impact
2. **2 hours**: Create hotfix branch and develop fix
3. **4 hours**: Test fix in staging
4. **6 hours**: Deploy to production
5. **24 hours**: Post-incident review
6. **48 hours**: Publish security advisory (coordinated disclosure)

## Resources

- [Semantic Versioning](https://semver.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Deployment Guide](docs/PRODUCTION_DEPLOYMENT_GUIDE.md)
- [Operations Runbook](docs/OPERATIONS_RUNBOOK.md)

---

**Last Updated**: November 2025  
Made with ❤️ by ISDATA Consulting
