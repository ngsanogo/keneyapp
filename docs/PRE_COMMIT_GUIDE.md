# Pre-commit Hook Guide

This guide explains how to set up and use pre-commit hooks in KeneyApp to automatically format, lint, and validate your code before every commit.

## Quick Start

### Windows (PowerShell)
```powershell
.\scripts\setup_pre_commit.ps1
```

### Linux/macOS
```bash
chmod +x scripts/setup_pre_commit.sh
./scripts/setup_pre_commit.sh
```

That's it! Pre-commit will now run automatically before every commit.

## What Gets Checked

Pre-commit automatically runs these checks before each commit:

### Python (Backend)
- **Black** - Code formatting (88 char line length)
- **isort** - Import sorting
- **Flake8** - Linting and style checks
- **mypy** - Type checking (gradual)
- **Bandit** - Security vulnerability scanning

### JavaScript/TypeScript (Frontend)
- **Prettier** - Code formatting
- **ESLint** - Linting and best practices

### General
- **Trailing whitespace** - Removes trailing spaces
- **End of file fixer** - Ensures files end with newline
- **YAML/JSON validation** - Checks syntax
- **Large files** - Prevents commits over 1MB
- **Merge conflicts** - Detects conflict markers
- **Private keys** - Prevents committing secrets
- **Dockerfile linting** - Validates Docker files
- **Markdown linting** - Formats markdown files

### Commit Messages
- **Conventional commits** - Enforces commit message format
  - `feat:` - New features
  - `fix:` - Bug fixes
  - `docs:` - Documentation changes
  - `style:` - Formatting (no code change)
  - `refactor:` - Code refactoring
  - `test:` - Adding tests
  - `chore:` - Maintenance tasks

## Manual Commands

### Run all checks manually
```powershell
# Windows
pre-commit run --all-files

# Linux/macOS
pre-commit run --all-files
```

### Format all code
```powershell
# Windows
.\scripts\format_all.ps1

# Check formatting without changes
.\scripts\format_all.ps1 -Check

# Linux/macOS
./scripts/format_all.sh
```

### Lint all code
```powershell
# Windows
.\scripts\lint_all.ps1

# Auto-fix issues
.\scripts\lint_all.ps1 -Fix

# Strict mode (fail on warnings)
.\scripts\lint_all.ps1 -Strict

# Linux/macOS
./scripts/lint_all.sh
```

### Update pre-commit hooks
```bash
pre-commit autoupdate
```

### Skip hooks (not recommended)
```bash
git commit --no-verify
```

## Installation Options

### Full installation (recommended)
```powershell
.\scripts\setup_pre_commit.ps1
```

### Force reinstall (if hooks are misbehaving)
```powershell
.\scripts\setup_pre_commit.ps1 -Force
```

### Skip package installation (if already installed)
```powershell
.\scripts\setup_pre_commit.ps1 -SkipInstall
```

## Workflow

### First-time setup
1. Clone the repository
2. Run setup script: `.\scripts\setup_pre_commit.ps1`
3. Make your changes
4. Commit as usual: `git commit -m "feat: add new feature"`
5. Pre-commit runs automatically and fixes what it can
6. If fixes were made, review and commit again
7. Push to remote

### Daily workflow
1. Make code changes
2. Run `git add` to stage files
3. Run `git commit` - hooks run automatically
4. If all checks pass, commit succeeds
5. If checks fail or auto-fix, review changes and commit again

### Before pushing
```powershell
# Format everything
.\scripts\format_all.ps1

# Lint everything
.\scripts\lint_all.ps1

# Run all pre-commit checks
pre-commit run --all-files

# Commit and push
git add .
git commit -m "chore: format and lint code"
git push
```

## Troubleshooting

### Pre-commit is slow
Pre-commit caches hook environments. First run is slow, subsequent runs are fast.

```bash
# Clear cache if needed
pre-commit clean
pre-commit install-hooks
```

### Hooks not running
```bash
# Reinstall hooks
pre-commit install --install-hooks --overwrite
pre-commit install --hook-type commit-msg --overwrite
```

### False positives
Some files may need to be excluded:

```yaml
# Add to .pre-commit-config.yaml
exclude: |
    (?x)^(
        path/to/file\.py|
        generated/.*
    )$
```

### Skip specific hooks temporarily
```bash
# Skip specific hook
SKIP=flake8 git commit -m "message"

# Skip all hooks (emergency only)
git commit --no-verify -m "message"
```

### Python version conflicts
Pre-commit uses Python 3.11. If you have multiple versions:

```yaml
# Update .pre-commit-config.yaml
language_version: python3.11  # or your version
```

## CI/CD Integration

Pre-commit runs in GitHub Actions automatically. Local checks match CI checks to prevent failures.

### Run CI checks locally
```powershell
# All checks
make ci

# Just linting
make lint

# Just tests
make test
```

## Best Practices

1. **Always run setup after cloning** - Ensures consistent environment
2. **Don't skip hooks** - They catch issues early
3. **Review auto-fixes** - Understand what changed
4. **Update regularly** - `pre-commit autoupdate` monthly
5. **Add exclusions carefully** - Don't bypass quality checks
6. **Fix issues, don't ignore** - Improves code quality
7. **Use conventional commits** - Enables automatic changelogs

## Configuration Files

- `.pre-commit-config.yaml` - Pre-commit configuration
- `pyproject.toml` - Black, isort, bandit configuration
- `mypy.ini` - Type checking configuration
- `.flake8` or `setup.cfg` - Flake8 configuration
- `frontend/.prettierrc` - Prettier configuration
- `frontend/.eslintrc` - ESLint configuration

## Advanced Usage

### Add custom hooks
Edit `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: custom-check
      name: Custom Check
      entry: python scripts/custom_check.py
      language: system
      pass_filenames: false
```

### Run specific hook
```bash
pre-commit run black --all-files
pre-commit run flake8 --all-files
```

### Run on specific files
```bash
pre-commit run --files app/routers/patients.py
```

### Debug hook issues
```bash
pre-commit run --verbose --all-files
```

## Help & Support

- **Pre-commit docs**: https://pre-commit.com/
- **Project docs**: `docs/DEVELOPMENT.md`
- **CI/CD guide**: `docs/CI_CD_GUIDE.md`

For issues, check:
1. Python version (3.11+)
2. Git hooks installed (`ls .git/hooks/`)
3. Pre-commit version (`pre-commit --version`)
4. Hook cache (try `pre-commit clean`)
