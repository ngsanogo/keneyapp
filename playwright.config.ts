import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Test Configuration for KeneyApp
 *
 * Tests critical user flows:
 * - Authentication & Authorization
 * - Patient management (CRUD)
 * - Messaging v3.0 (secure communication)
 * - Document management v3.0 (upload, view, share)
 * - Medical record sharing v3.0 (with PIN)
 *
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './e2e',

  /* Run tests in files in parallel - DISABLED to prevent timeout */
  fullyParallel: false,

  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,

  /* Opt out of parallel tests on CI - force sequential */
  workers: 1,

  /* Reporter to use */
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/e2e-results.json' }],
    ['junit', { outputFile: 'test-results/e2e-junit.xml' }],
    ['list']
  ],

  /* Shared settings for all the projects below */
  use: {
    /* Base URL to use in actions like `await page.goto('/')` */
    baseURL: process.env.BASE_URL || 'http://localhost:3000',

    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',

    /* Take screenshot on failure */
    screenshot: 'only-on-failure',

    /* Record video on failure */
    video: 'retain-on-failure',

    /* Maximum time each action can take - reduced to prevent hanging */
    actionTimeout: 10000,

    /* Maximum time each navigation can take - reduced */
    navigationTimeout: 15000,
  },

  /* Configure projects for major browsers - ONLY Chromium for speed */
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        /* Add viewport for consistency */
        viewport: { width: 1280, height: 720 },
      },
    },

    /* DISABLED - Enable only when needed to prevent timeout
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    // Test against mobile viewports
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },

    // Test against branded browsers
    {
      name: 'Microsoft Edge',
      use: { ...devices['Desktop Edge'], channel: 'msedge' },
    },
    {
      name: 'Google Chrome',
      use: { ...devices['Desktop Chrome'], channel: 'chrome' },
    },
    */
  ],

  /* Run your local dev server before starting the tests */
  webServer: process.env.SKIP_WEBSERVER ? undefined : {
    command: 'cd frontend && npm start',
    url: 'http://localhost:3000',
    reuseExistingServer: true,
    timeout: 60000, // Reduced from 120s
    stdout: 'pipe',
    stderr: 'pipe',
  },

  /* Global timeout for each test - reduced to prevent hanging */
  timeout: 30000,

  /* Expected HTTP responses */
  expect: {
    timeout: 10000,
    toHaveScreenshot: {
      maxDiffPixels: 100,
    },
  },

  /* Output folder for test artifacts */
  outputDir: 'test-results/',
});
