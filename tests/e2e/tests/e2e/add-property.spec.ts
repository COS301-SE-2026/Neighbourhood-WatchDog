import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {

  //checking the happy case
  await page.goto('http://localhost:3000/dashboard');
  await page.getByRole('button', { name: 'Add Property' }).click();
  await page.getByRole('textbox', { name: 'Address Line 1 (Street' }).click();
  await page.getByRole('textbox', { name: 'Address Line 1 (Street' }).fill('21 Fake Street');
  await page.getByRole('textbox', { name: 'Address Line 2 (Apartment,' }).click();
  await page.getByRole('textbox', { name: 'Address Line 2 (Apartment,' }).fill('221');
  await page.getByRole('textbox', { name: 'Address Line 2 (Apartment,' }).press('ArrowLeft');
  await page.getByRole('textbox', { name: 'Address Line 2 (Apartment,' }).press('ArrowLeft');
  await page.getByRole('textbox', { name: 'Address Line 2 (Apartment,' }).press('ArrowRight');
  await page.getByRole('textbox', { name: 'Address Line 2 (Apartment,' }).press('ArrowRight');
  await page.getByRole('textbox', { name: 'Address Line 2 (Apartment,' }).fill('Unit 21');
  await page.getByRole('textbox', { name: 'City' }).click();
  await page.getByRole('textbox', { name: 'City' }).fill('Pretoria');
  await page.getByLabel('Province').selectOption('Eastern Cape');
  await page.getByRole('textbox', { name: 'Postal Code' }).click();
  await page.getByRole('textbox', { name: 'Postal Code' }).fill('0987');
  await page.getByRole('button', { name: 'Create Property' }).click();
  
  // trying to add without credentials
  await page.getByRole('button', { name: 'Add Property' }).click();
  await page.getByRole('button', { name: 'Create Property' }).dblclick();
  await page.getByRole('textbox', { name: 'Address Line 1 (Street' }).click();
  await page.getByRole('button', { name: 'Cancel' }).click();

  //Check that it closes when the close button is clicked
  await page.getByRole('button', { name: 'Add Property' }).click();
  await page.getByRole('button', { name: 'Close' }).click();
});