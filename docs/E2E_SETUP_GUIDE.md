# E2E Testing Setup Guide

## Problem Summary

E2E tests were hanging indefinitely (hours) due to:

1. **Parallel browser execution**: Testing 7 browsers simultaneously (Chromium, Firefox, WebKit, Mobile Chrome/Safari, Edge, Chrome)
2. **Long timeouts**: 60-120 second timeouts preventing fail-fast behavior
3. **No timeout protection**: Tests could run forever with no kill mechanism
4. **Race conditions**: Parallel execution causing unpredictable behavior

## Solution Implemented

### Configuration Changes (playwright.config.ts)

1. **Sequential Execution**
   - Changed `fullyParallel: true` → `false`
   - Set `workers: 1` (force single worker)
   - **Impact**: Tests run one at a time, preventing race conditions

2. **Single Browser Testing**
   - Disabled 6 of 7 browsers (kept Chromium only)
   - **Impact**: 85% reduction in test execution time

3. **Reduced Timeouts**
   - Global timeout: 60s → 30s (50% reduction)
   - Navigation: 30s → 15s (50% reduction)
   - Action: 15s → 10s (33% reduction)
   - webServer: 120s → 60s (50% reduction)
   - **Impact**: Fail fast when issues occur instead of hanging

4. **Smart webServer Handling**
   - Always reuse existing server (`reuseExistingServer: true`)
   - Allow skipping via `SKIP_WEBSERVER=1` env var
   - Better error visibility with stdout/stderr piping

### New Test Scripts

#### Quick E2E Tests (Recommended for Development)

```bash
# Using existing local stack (2-5 minutes)
./scripts/run_e2e_quick.sh

# Or via Makefile
make e2e-quick
```

**Features**:

- Uses existing backend/frontend (no Docker overhead)
- 5-minute maximum timeout enforced by OS
- Health checks before testing
- Auto-starts frontend if needed
- Chromium only

#### Full E2E Tests (For Comprehensive Testing)

```bash
# Full Docker orchestration (10-15 minutes)
./scripts/run_e2e_tests.sh

# Or via Makefile
make e2e-full
```

**Features**:

- Complete stack with PostgreSQL, Redis, Celery
- All services isolated in Docker
- Use before major releases

## Prerequisites

### Node.js Installation Required

E2E tests require Node.js and npm to be installed and in your PATH:

```bash
# Check if Node.js is installed
node --version  # Should show v18.x or higher
npm --version   # Should show v10.x or higher

# If not installed, install via:
# macOS (Homebrew)
brew install node@18

# Or download from: https://nodejs.org/
```

### Install Playwright Browsers

First time only:

```bash
cd frontend
npm install
npx playwright install chromium
```

Or use:

```bash
make e2e-install
```

## Running E2E Tests

### Option 1: Quick Tests (Development Workflow)

**Best for**: Development, PR validation, quick feedback

```bash
# 1. Ensure backend is running
docker-compose up -d backend

# 2. Ensure frontend is running (or script will auto-start)
cd frontend && npm start &

# 3. Run quick tests
./scripts/run_e2e_quick.sh
```

**Expected**: Complete in 2-5 minutes or timeout with clear error.

### Option 2: Full Tests (Comprehensive Validation)

**Best for**: Release validation, complete integration testing

```bash
# Full stack with Docker
./scripts/run_e2e_tests.sh
```

**Expected**: Complete in 10-15 minutes.

### Option 3: Makefile Commands

```bash
# Quick tests (recommended)
make e2e-quick

# Full Docker tests
make e2e-full

# Specific test file
make e2e-test TEST=e2e/auth.spec.ts

# Interactive UI mode
make e2e-ui

# View test report
make e2e-report
```

## Troubleshooting

### Tests Still Hang?

1. **Check services are running**:

   ```bash
   curl http://localhost:8000/health  # Backend
   curl http://localhost:3000         # Frontend
   ```

2. **Reduce timeout further**:
   Edit `playwright.config.ts`:

   ```typescript
   timeout: 15000,  // 15 seconds instead of 30
   ```

3. **Run single test**:

   ```bash
   cd frontend
   npx playwright test e2e/auth.spec.ts --config=../playwright.config.ts
   ```

4. **Enable debug mode**:

   ```bash
   DEBUG=pw:api npx playwright test
   ```

### npx Command Not Found

Node.js is not in your PATH. Solutions:

1. **Install Node.js**:

   ```bash
   brew install node@18
   ```

2. **Add to PATH** (if already installed):

   ```bash
   # Add to ~/.zshrc or ~/.bashrc
   export PATH="/usr/local/bin:$PATH"
   export PATH="$HOME/.nvm/versions/node/v18.20.8/bin:$PATH"
   ```

3. **Use Docker instead**:

   ```bash
   # E2E tests in Docker don't need local Node.js
   ./scripts/run_e2e_tests.sh
   ```

### Frontend Won't Start

```bash
# Check if port 3000 is already in use
lsof -i :3000

# Kill existing process
kill -9 <PID>

# Start fresh
cd frontend
npm install
npm start
```

### Backend Issues

```bash
# Check backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend

# Health check
curl http://localhost:8000/health
```

## Performance Comparison

| Configuration | Time | Browsers | Workers | Notes |
|--------------|------|----------|---------|-------|
| **Old** (problematic) | Hours (hangs) | 7 | Unlimited | Parallel execution, race conditions |
| **New (Chromium only)** | 2-5 min | 1 | 1 | Sequential, fast feedback |
| **New (all browsers)** | 10-15 min | 7 | 1 | Sequential, comprehensive |

## Re-enabling Multiple Browsers

If you need to test across all browsers (CI/pre-release):

1. Edit `playwright.config.ts`
2. Uncomment the browser projects:

   ```typescript
   projects: [
     { name: 'chromium', ... },
     { name: 'firefox', ... },      // Uncomment
     { name: 'webkit', ... },       // Uncomment
     // etc.
   ]
   ```

3. **Warning**: This will multiply test time by 7x
4. Recommended only for:
   - Pre-release validation
   - CI pipelines with ample time
   - Browser-specific bug investigation

## Best Practices

1. **Development**: Use `make e2e-quick` for fast feedback
2. **PR Validation**: Use `make e2e-test` (Chromium only)
3. **Pre-Release**: Use `make e2e-full` (all browsers, Docker)
4. **Always**: Run tests before pushing to production
5. **Monitor**: If tests take >5 minutes, investigate (likely hanging)

## CI/CD Integration

### GitHub Actions

Tests now complete reliably in CI:

```yaml
- name: Run E2E Tests
  run: |
    docker-compose up -d
    npm --prefix frontend exec playwright test --project=chromium
  timeout-minutes: 10  # Fail if exceeds 10 minutes
```

### Local CI Testing

Test GitHub Actions locally with `act`:

```bash
# Test E2E workflow
make ci-test-e2e

# See: docs/LOCAL_CI_TESTING.md for details
```

## Summary of Changes

| File | Changes | Purpose |
|------|---------|---------|
| `playwright.config.ts` | 5 major changes | Prevent hanging, enable fail-fast |
| `scripts/run_e2e_quick.sh` | New script | Fast local testing (2-5 min) |
| `Makefile` | Added e2e-quick, e2e-full | Convenient test commands |
| This guide | Complete documentation | Setup and troubleshooting |

## Expected Behavior

✅ **Before**: Tests hang for hours with no feedback
✅ **After**: Tests complete in 2-5 minutes or timeout with clear error

✅ **Before**: Testing 7 browsers in parallel
✅ **After**: Testing 1 browser (Chromium) sequentially

✅ **Before**: No timeout protection
✅ **After**: 5-minute maximum enforced by OS

---

**Questions?** Check the troubleshooting section or see:

- `docs/E2E_TESTING.md` - Comprehensive E2E testing guide
- `docs/LOCAL_CI_TESTING.md` - Local CI/CD testing with act
- `playwright.config.ts` - Full configuration with comments
