import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('http://localhost:3000/dashboard');
  await page.getByRole('button', { name: 'Add Camera' }).click();
  await page.getByRole('textbox', { name: 'Camera Location' }).click();
  await page.getByRole('textbox', { name: 'Camera Location' }).fill('Backyard');
  await page.getByRole('textbox', { name: 'RTSP URL' }).click();
  await page.getByRole('textbox', { name: 'RTSP URL' }).fill('rtsp://Intrepid:password1234@172.20.10.2:554/stream2');
  await page.getByRole('button', { name: 'Acknowledge' }).click();
});