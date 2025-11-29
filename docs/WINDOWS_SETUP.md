# Windows Quick Setup Guide

## TL;DR - Quick Commands

```powershell
# 1. Enable script execution (one-time, run as yourself)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 2. Add Python Scripts to PATH (for this session)
$env:Path += ";$env:APPDATA\Python\Python313\Scripts"

# 3. Install tools
python -m pip install --user pre-commit black flake8 isort mypy bandit

# 4. Format and lint
.\scripts\format_all.ps1
.\scripts\lint_all.ps1
```

## Initial Setup (One-Time)

### 1. Enable PowerShell Script Execution

Windows blocks script execution by default. Enable it:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**What this does:** Allows you to run locally created scripts while still requiring downloaded scripts to be signed.

### 2. Add Python Scripts to PATH

Python tools install to `%APPDATA%\Python\Python313\Scripts` but this isn't on PATH by default.

**Temporary (current session only):**
```powershell
$env:Path += ";$env:APPDATA\Python\Python313\Scripts"
```

**Permanent (recommended):**
```powershell
# Add to your PowerShell profile
if (-not (Test-Path $PROFILE)) {
    New-Item -Path $PROFILE -ItemType File -Force
}
Add-Content $PROFILE '$env:Path += ";$env:APPDATA\Python\Python313\Scripts"'
```

Or add manually via System Properties → Environment Variables → User variables → Path

### 3. Install Development Tools

```powershell
python -m pip install --user pre-commit black flake8 isort mypy bandit
```

## Daily Workflow

### Format Code Before Committing

```powershell
# Auto-fix all formatting
.\scripts\format_all.ps1

# Check formatting without changes
.\scripts\format_all.ps1 -Check
```

### Lint Code

```powershell
# Check for issues
.\scripts\lint_all.ps1

# Auto-fix where possible
.\scripts\lint_all.ps1 -Fix

# Strict mode (fail on warnings)
.\scripts\lint_all.ps1 -Strict
```

### Commit Changes

```powershell
git add .
git commit -m "feat: your commit message"
git push
```

## Alternative: Use Pre-commit Hooks

If you want automatic checks on every commit:

```powershell
# Quick setup (hooks installed, environments installed on-demand)
.\scripts\setup_pre_commit_quick.ps1

# Or full setup (downloads all hook environments - takes 5-10 minutes)
.\scripts\setup_pre_commit.ps1
```

**Pros:**
- Automatic checks on every commit
- Can't forget to format/lint
- Matches CI/CD exactly

**Cons:**
- First commit slow (installs hook environments)
- Can be interrupted with Ctrl+C (hooks still install on next commit)
- Harder to debug if hooks fail

## Troubleshooting

### "Script execution is disabled"

```
UnauthorizedAccess: .\scripts\setup_pre_commit.ps1
```

**Fix:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "pre-commit: command not found"

The Python Scripts folder isn't on PATH.

**Fix (temporary):**
```powershell
$env:Path += ";$env:APPDATA\Python\Python313\Scripts"
```

**Fix (permanent):**
Add `C:\Users\<YourUsername>\AppData\Roaming\Python\Python313\Scripts` to your system PATH.

### "make: command not found"

Make isn't available on Windows by default. Use direct PowerShell scripts instead:

| Makefile Command | Windows PowerShell Equivalent |
|------------------|-------------------------------|
| `make format` | `.\scripts\format_all.ps1` |
| `make format-check` | `.\scripts\format_all.ps1 -Check` |
| `make lint` | `.\scripts\lint_all.ps1` |
| `make lint-fix` | `.\scripts\lint_all.ps1 -Fix` |
| `make setup-pre-commit` | `.\scripts\setup_pre_commit_quick.ps1` |

Or install Make for Windows:
- **Chocolatey:** `choco install make`
- **Scoop:** `scoop install make`
- **Manual:** Download from [GnuWin32](http://gnuwin32.sourceforge.net/packages/make.htm)

### Pre-commit is slow / hangs

Pre-commit downloads and caches hook environments. First run takes 5-10 minutes.

**If it hangs:**
1. Press Ctrl+C to cancel
2. Use the quick setup instead: `.\scripts\setup_pre_commit_quick.ps1`
3. Hook environments will install on first commit (slower, but works)

**Or skip pre-commit entirely:**
- Just use `.\scripts\format_all.ps1` and `.\scripts\lint_all.ps1` manually before commits

### Prettier/ESLint errors (frontend)

If you don't have Node.js/npm installed, frontend formatting will fail. This is OK if you're only working on backend.

**To fix:**
1. Install Node.js: https://nodejs.org/
2. Install frontend dependencies: `cd frontend; npm install`
3. Re-run: `.\scripts\format_all.ps1`

**Or skip frontend:**
```powershell
# Format only Python code
black app tests
isort app tests
```

## Recommended Workflow (Windows)

1. **One-time setup:**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   $env:Path += ";$env:APPDATA\Python\Python313\Scripts"
   python -m pip install --user pre-commit black flake8 isort mypy bandit
   ```

2. **Before every commit:**
   ```powershell
   .\scripts\format_all.ps1
   .\scripts\lint_all.ps1
   ```

3. **Commit and push:**
   ```powershell
   git add .
   git commit -m "feat: your changes"
   git push
   ```

That's it! No make, no pre-commit hooks, just simple PowerShell scripts.

## Advanced: PowerShell Aliases

Add to your PowerShell profile (`$PROFILE`) for shorter commands:

```powershell
# Formatting aliases
function Format-Code { .\scripts\format_all.ps1 }
function Format-Check { .\scripts\format_all.ps1 -Check }
function Lint-Code { .\scripts\lint_all.ps1 }
function Lint-Fix { .\scripts\lint_all.ps1 -Fix }

Set-Alias fmt Format-Code
Set-Alias lint Lint-Code
```

Then use:
```powershell
fmt      # Format all code
lint     # Lint all code
```

## CI/CD Note

The CI pipeline runs the same checks. If your local format/lint passes, CI will pass too.

```powershell
# Local checks (fast)
.\scripts\format_all.ps1 -Check
.\scripts\lint_all.ps1

# If both pass, CI will pass ✓
```
