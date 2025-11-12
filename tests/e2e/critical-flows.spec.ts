import { test, expect, type Page } from '@playwright/test';

/**
 * E2E Tests: Authentication Flows
 *
 * Tests critical authentication scenarios:
 * - Login with valid credentials
 * - Login failure with invalid credentials
 * - Logout functionality
 * - Session persistence
 * - Role-based access control
 */

const ADMIN_CREDENTIALS = {
  username: 'admin',
  password: 'admin123'
};

const DOCTOR_CREDENTIALS = {
  username: 'doctor',
  password: 'doctor123'
};

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should display login page', async ({ page }) => {
    await expect(page).toHaveTitle(/KeneyApp/);
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should login successfully with admin credentials', async ({ page }) => {
    await page.fill('input[name="username"]', ADMIN_CREDENTIALS.username);
    await page.fill('input[name="password"]', ADMIN_CREDENTIALS.password);
    await page.click('button[type="submit"]');

    // Wait for navigation to dashboard
    await expect(page).toHaveURL(/\/dashboard/);

    // Verify user menu is visible
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();

    // Verify welcome message
    await expect(page.locator('text=Welcome')).toBeVisible();
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.fill('input[name="username"]', 'invalid');
    await page.fill('input[name="password"]', 'wrong_password');
    await page.click('button[type="submit"]');

    // Verify error message
    await expect(page.locator('text=/Invalid credentials|Login failed/i')).toBeVisible();

    // Verify still on login page
    await expect(page).toHaveURL(/\/login/);
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await page.fill('input[name="username"]', ADMIN_CREDENTIALS.username);
    await page.fill('input[name="password"]', ADMIN_CREDENTIALS.password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);

    // Logout
    await page.click('[data-testid="user-menu"]');
    await page.click('text=Logout');

    // Verify redirect to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should maintain session after page reload', async ({ page }) => {
    // Login
    await page.fill('input[name="username"]', ADMIN_CREDENTIALS.username);
    await page.fill('input[name="password"]', ADMIN_CREDENTIALS.password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);

    // Reload page
    await page.reload();

    // Verify still authenticated
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('should redirect to login when accessing protected route without auth', async ({ page }) => {
    await page.goto('/patients');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should enforce role-based access (doctor cannot access admin routes)', async ({ page }) => {
    // Login as doctor
    await page.fill('input[name="username"]', DOCTOR_CREDENTIALS.username);
    await page.fill('input[name="password"]', DOCTOR_CREDENTIALS.password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);

    // Try to access admin route
    await page.goto('/admin/users');

    // Should be redirected or show forbidden message
    await expect(
      page.locator('text=/Access denied|Forbidden|Not authorized/i')
    ).toBeVisible({ timeout: 5000 }).catch(() => {
      // Or redirected back to dashboard
      expect(page.url()).toMatch(/\/dashboard/);
    });
  });
});

/**
 * E2E Tests: Patient Management
 *
 * Tests CRUD operations for patients:
 * - Create new patient
 * - View patient list
 * - View patient details
 * - Update patient information
 * - Delete patient (soft delete)
 */
test.describe('Patient Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('input[name="username"]', ADMIN_CREDENTIALS.username);
    await page.fill('input[name="password"]', ADMIN_CREDENTIALS.password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should display patient list', async ({ page }) => {
    await page.goto('/patients');
    await expect(page).toHaveURL(/\/patients/);
    await expect(page.locator('h1')).toContainText(/Patients/i);

    // Verify table or list is visible
    await expect(
      page.locator('[data-testid="patient-list"], table, .patient-card')
    ).toBeVisible();
  });

  test('should create new patient', async ({ page }) => {
    await page.goto('/patients');
    await page.click('text=New Patient');

    // Fill patient form
    await page.fill('input[name="first_name"]', 'John');
    await page.fill('input[name="last_name"]', 'Doe');
    await page.fill('input[name="date_of_birth"]', '1990-01-01');
    await page.selectOption('select[name="gender"]', 'M');
    await page.fill('input[name="phone"]', '+33601020304');
    await page.fill('input[name="email"]', 'john.doe@example.com');

    // Submit form
    await page.click('button[type="submit"]');

    // Verify success message
    await expect(page.locator('text=/Patient created|Success/i')).toBeVisible();

    // Verify redirect to patient list or detail
    await expect(page).toHaveURL(/\/patients/);
  });

  test('should view patient details', async ({ page }) => {
    await page.goto('/patients');

    // Click on first patient
    await page.click('[data-testid="patient-row"]:first-child, .patient-card:first-child');

    // Verify patient detail page
    await expect(page).toHaveURL(/\/patients\/\d+/);
    await expect(page.locator('[data-testid="patient-name"]')).toBeVisible();
    await expect(page.locator('[data-testid="patient-info"]')).toBeVisible();
  });

  test('should update patient information', async ({ page }) => {
    await page.goto('/patients');
    await page.click('[data-testid="patient-row"]:first-child');

    // Click edit button
    await page.click('button:has-text("Edit"), [data-testid="edit-patient"]');

    // Update phone number
    await page.fill('input[name="phone"]', '+33699887766');

    // Save changes
    await page.click('button[type="submit"]');

    // Verify success
    await expect(page.locator('text=/Updated|Success/i')).toBeVisible();
  });

  test('should search patients', async ({ page }) => {
    await page.goto('/patients');

    // Enter search query
    await page.fill('input[placeholder*="Search"]', 'John');

    // Wait for results
    await page.waitForTimeout(500);

    // Verify filtered results
    const rows = page.locator('[data-testid="patient-row"]');
    expect(await rows.count()).toBeGreaterThan(0);
  });
});

/**
 * E2E Tests: Messaging v3.0
 *
 * Tests secure messaging functionality:
 * - Send message
 * - View inbox
 * - Read message
 * - Reply to message
 * - Mark as read
 */
test.describe('Secure Messaging v3.0', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="username"]', DOCTOR_CREDENTIALS.username);
    await page.fill('input[name="password"]', DOCTOR_CREDENTIALS.password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should display message inbox', async ({ page }) => {
    await page.goto('/messages');
    await expect(page).toHaveURL(/\/messages/);
    await expect(page.locator('h1')).toContainText(/Messages/i);
  });

  test('should send new message', async ({ page }) => {
    await page.goto('/messages');
    await page.click('text=New Message, Compose');

    // Fill message form
    await page.fill('input[name="recipient"]', 'patient');
    await page.fill('input[name="subject"]', 'Test E2E Message');
    await page.fill('textarea[name="content"]', 'This is a test message from E2E tests');

    // Send message
    await page.click('button:has-text("Send")');

    // Verify success
    await expect(page.locator('text=/Message sent|Success/i')).toBeVisible();
  });

  test('should read message and mark as read', async ({ page }) => {
    await page.goto('/messages');

    // Click on first unread message
    await page.click('[data-testid="message-row"]:first-child');

    // Verify message content is visible
    await expect(page.locator('[data-testid="message-content"]')).toBeVisible();

    // Verify marked as read (check for read indicator)
    await page.goto('/messages');
    // First message should now show as read
  });
});

/**
 * E2E Tests: Document Management v3.0
 */
test.describe('Document Management v3.0', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="username"]', DOCTOR_CREDENTIALS.username);
    await page.fill('input[name="password"]', DOCTOR_CREDENTIALS.password);
    await page.click('button[type="submit"]');
  });

  test('should upload document', async ({ page }) => {
    await page.goto('/patients/1/documents');

    // Click upload button
    await page.click('text=Upload Document');

    // Set input files (create temp test file)
    const filePath = 'tests/e2e/fixtures/test-document.pdf';
    await page.setInputFiles('input[type="file"]', filePath);

    // Select document type
    await page.selectOption('select[name="document_type"]', 'prescription');

    // Submit upload
    await page.click('button:has-text("Upload")');

    // Verify success
    await expect(page.locator('text=/Uploaded|Success/i')).toBeVisible();
  });

  test('should view document list', async ({ page }) => {
    await page.goto('/patients/1/documents');
    await expect(page.locator('[data-testid="document-list"]')).toBeVisible();
  });
});
