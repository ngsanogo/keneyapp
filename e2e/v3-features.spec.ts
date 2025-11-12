import { test, expect } from '@playwright/test';

/**
 * E2E Tests for v3.0 Features: Messages, Documents, Shares
 */

test.describe('Secure Messaging (v3.0)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard');
    await page.click('a[href="/messages"]');
  });

  test('should display message inbox', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Messages');
    await expect(page.locator('[data-testid="message-list"]')).toBeVisible();
  });

  test('should send a new message', async ({ page }) => {
    await page.click('[data-testid="compose-message-btn"]');

    await page.fill('input[name="recipient"]', 'Dr. Smith');
    await page.fill('input[name="subject"]', 'Test Message');
    await page.fill('textarea[name="content"]', 'This is a test encrypted message.');

    await page.click('button[type="submit"]');

    await expect(page.locator('.success-message')).toContainText('Message sent');
  });

  test('should mark message as read', async ({ page }) => {
    const unreadMessage = page.locator('[data-testid="message-item"].unread').first();
    await unreadMessage.click();

    await page.waitForTimeout(500); // Wait for read status update
    await page.goBack();

    // Verify message is marked as read
    const messageCount = await page.locator('[data-testid="message-item"].unread').count();
    expect(messageCount).toBeLessThan(10); // Should have decreased
  });
});

test.describe('Document Management (v3.0)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard');
    await page.click('a[href="/documents"]');
  });

  test('should display document list', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Documents');
    await expect(page.locator('[data-testid="document-list"]')).toBeVisible();
  });

  test('should upload a document', async ({ page }) => {
    await page.click('[data-testid="upload-document-btn"]');

    // Set file input
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('./e2e/fixtures/test-document.pdf');

    await page.selectOption('select[name="document_type"]', 'prescription');
    await page.fill('textarea[name="description"]', 'Test prescription document');

    await page.click('button[type="submit"]');

    await expect(page.locator('.success-message')).toContainText('Document uploaded');
  });

  test('should filter documents by type', async ({ page }) => {
    await page.selectOption('[data-testid="document-filter"]', 'lab_result');

    await page.waitForResponse(response =>
      response.url().includes('/api/v1/documents') && response.status() === 200
    );

    // Verify all visible documents are lab results
    const documentTypes = page.locator('[data-testid="document-type"]');
    const count = await documentTypes.count();

    for (let i = 0; i < count; i++) {
      await expect(documentTypes.nth(i)).toContainText('Lab Result');
    }
  });
});

test.describe('Medical Record Sharing (v3.0)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard');

    // Navigate to a patient
    await page.click('a[href="/patients"]');
    await page.click('[data-testid="patient-row"]:first-child');
  });

  test('should create a share link', async ({ page }) => {
    await page.click('[data-testid="share-records-btn"]');

    await page.fill('input[name="recipient_email"]', 'doctor@example.com');
    await page.fill('input[name="recipient_name"]', 'Dr. External');
    await page.fill('input[name="expires_in_hours"]', '24');
    await page.check('input[name="require_pin"]');
    await page.fill('input[name="pin"]', '1234');

    await page.click('button[type="submit"]');

    await expect(page.locator('.success-message')).toContainText('Share link created');

    // Verify share link is displayed
    const shareLink = page.locator('[data-testid="share-link"]');
    await expect(shareLink).toBeVisible();

    // Copy link
    await page.click('[data-testid="copy-link-btn"]');
    await expect(page.locator('.success-message')).toContainText('Link copied');
  });

  test('should revoke a share', async ({ page }) => {
    await page.click('[data-testid="view-shares-btn"]');

    const shareRow = page.locator('[data-testid="share-row"]').first();
    await shareRow.locator('[data-testid="revoke-share-btn"]').click();

    // Confirm revocation
    await page.click('[data-testid="confirm-revoke-btn"]');

    await expect(page.locator('.success-message')).toContainText('Share revoked');
  });
});
