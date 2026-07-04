import { test, expect } from '@playwright/test';

test('Загрузка PDF и поиск', async ({ page }) => {
  await page.goto('/');

  await expect(page.locator('text=Поиск по документам')).toBeVisible();

  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles('./e2e/fixtures/test.pdf');

  await page.waitForSelector('text=Готово', { timeout: 30000 });

  await page.fill('input[placeholder="Введите запрос..."]', 'Elasticsearch');
  await page.click('button:has-text("Найти")');

  await page.waitForSelector('.result-card', { timeout: 10000 });

  const resultCards = page.locator('.result-card');
  await expect(resultCards).not.toHaveCount(0);
});