import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Patient Management
 */

test.describe('Patient Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard');

    // Navigate to patients
    await page.click('a[href="/patients"]');
    await page.waitForURL('**/patients');
  });

  test('should display patient list', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Patients');
    await expect(page.locator('[data-testid="patient-table"]')).toBeVisible();
  });

  test('should create a new patient', async ({ page }) => {
    // Click add patient button
    await page.click('[data-testid="add-patient-btn"]');

    // Fill patient form
    await page.fill('input[name="first_name"]', 'John');
    await page.fill('input[name="last_name"]', 'Doe');
    await page.fill('input[name="date_of_birth"]', '1990-01-01');
    await page.selectOption('select[name="gender"]', 'M');
    await page.fill('input[name="phone"]', '+33612345678');
    await page.fill('input[name="email"]', 'john.doe@test.com');

    // Submit form
    await page.click('button[type="submit"]');

    // Verify success message
    await expect(page.locator('.success-message')).toContainText('Patient created successfully');

    // Verify patient appears in list
    await expect(page.locator('text=John Doe')).toBeVisible();
  });

  test('should search for patients', async ({ page }) => {
    // Enter search term
    await page.fill('input[data-testid="patient-search"]', 'John');

    // Wait for results
    await page.waitForResponse(response =>
      response.url().includes('/api/v1/patients') && response.status() === 200
    );

    // Verify filtered results
    const rows = page.locator('[data-testid="patient-row"]');
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should view patient details', async ({ page }) => {
    // Click on first patient
    await page.click('[data-testid="patient-row"]:first-child');

    // Verify detail page
    await expect(page.locator('[data-testid="patient-details"]')).toBeVisible();
    await expect(page.locator('h2')).toContainText('Patient Information');
  });

  test('should update patient information', async ({ page }) => {
    // Go to first patient
    await page.click('[data-testid="patient-row"]:first-child');

    // Click edit button
    await page.click('[data-testid="edit-patient-btn"]');

    // Update phone number
    const newPhone = '+33698765432';
    await page.fill('input[name="phone"]', newPhone);

    // Save changes
    await page.click('button[type="submit"]');

    // Verify success
    await expect(page.locator('.success-message')).toContainText('Patient updated');
    await expect(page.locator(`text=${newPhone}`)).toBeVisible();
  });

  test('should handle validation errors', async ({ page }) => {
    // Click add patient
    await page.click('[data-testid="add-patient-btn"]');

    // Submit without required fields
    await page.click('button[type="submit"]');

    // Verify error messages
    await expect(page.locator('.field-error')).toHaveCount(3); // first_name, last_name, date_of_birth
  });
});
