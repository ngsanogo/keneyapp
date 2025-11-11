# E2E Testing Setup Guide

This guide helps you set up and run end-to-end (E2E) tests for KeneyApp using Playwright.

## Prerequisites

- Node.js >= 18.0.0
- npm or yarn

## Installation

### 1. Install Node.js (if not already installed)

**macOS (using Homebrew):**
```bash
brew install node@18
```

**Or download from:** https://nodejs.org/

### 2. Install Dependencies

From the project root directory:

```bash
npm install
```

### 3. Install Playwright Browsers

```bash
npm run playwright:install
```

## Running E2E Tests

### Run All Tests
```bash
npm run test:e2e
```

### Run Tests in UI Mode (Interactive)
```bash
npm run test:e2e:ui
```

### Run Tests in Headed Mode (See Browser)
```bash
npm run test:e2e:headed
```

### Debug Tests
```bash
npm run test:e2e:debug
```

### Run Specific Test File
```bash
npx playwright test e2e/auth.spec.ts
```

### Run Specific Test by Name
```bash
npx playwright test -g "should login with valid credentials"
```

## Test Structure

```
e2e/
├── auth.spec.ts           # Authentication flow tests
├── patients.spec.ts       # Patient CRUD operations tests
└── v3-features.spec.ts    # v3.0 features (messaging, documents, shares)
```

## Configuration

The Playwright configuration is in `playwright.config.ts`. Key settings:

- **Base URL:** `http://localhost:3000` (override with `BASE_URL` env var)
- **Test timeout:** 60 seconds per test
- **Retries:** 2 on CI, 0 locally
- **Browsers:** Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari, Edge, Chrome
- **Screenshots:** Captured on failure
- **Videos:** Recorded on failure
- **Traces:** Captured on first retry

## Troubleshooting

### TypeScript Errors in E2E Files

If you see TypeScript errors like "Cannot find module '@playwright/test'":

1. Ensure dependencies are installed: `npm install`
2. Restart VS Code or reload the TypeScript server
3. Check that `tsconfig.json` exists at the project root

### Tests Failing to Connect

1. Ensure the backend is running: `uvicorn app.main:app --reload`
2. Ensure the frontend is running: `cd frontend && npm start`
3. Or use the E2E Docker setup: `./scripts/run_e2e_tests.sh`

### Port Already in Use

If port 3000 is in use, you can:
1. Change the port in the frontend
2. Override with `BASE_URL` environment variable:
   ```bash
   BASE_URL=http://localhost:3001 npm run test:e2e
   ```

## CI/CD Integration

E2E tests run automatically in GitHub Actions workflows. See:
- `.github/workflows/ci-enhanced.yml`
- `docker-compose.e2e.yml` for the E2E test environment

## Writing New E2E Tests

1. Create a new `.spec.ts` file in the `e2e/` directory
2. Import Playwright test utilities:
   ```typescript
   import { test, expect } from '@playwright/test';
   ```
3. Write test cases:
   ```typescript
   test('should do something', async ({ page }) => {
     await page.goto('/');
     await expect(page).toHaveTitle(/KeneyApp/);
   });
   ```
4. Run your test: `npx playwright test e2e/your-test.spec.ts`

## Best Practices

1. **Use data-testid attributes** for reliable selectors
2. **Wait for navigation** after form submissions
3. **Clean up test data** after tests (or use transactions)
4. **Use Page Object Model** for complex pages
5. **Keep tests independent** - don't rely on execution order
6. **Use beforeEach** for common setup (login, navigation)

## Additional Resources

- [Playwright Documentation](https://playwright.dev)
- [VS Code Playwright Extension](https://marketplace.visualstudio.com/items?itemName=ms-playwright.playwright)
- [KeneyApp E2E Test Scenarios](docs/E2E_TEST_SCENARIOS.md)
- [E2E Testing Quick Reference](docs/E2E_TESTING_QUICK_REF.md)
