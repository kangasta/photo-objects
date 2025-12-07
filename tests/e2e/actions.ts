import { expect, Page } from '@playwright/test';
import path from 'path';

export const login = async (page: Page) => {
  await page.goto('/');

  await page.getByText('Login').click();
  await page.getByLabel('Username').fill(process.env.USERNAME ?? '');
  await page.getByLabel('Password').fill(process.env.PASSWORD ?? '');
  await page.locator('form').getByText('Login').click();

  await expect(page.getByTitle('Logged in as admin')).toBeVisible();
}

// From https://stackoverflow.com/a/1349426/3311449
const withRandomSuffix = (prefix: string, length: number): string => {
  let suffix = '';
  const chars = 'bcdfghjklmnpqrstvwxz2456789'; // From Kubernetes random suffix
  let counter = 0;
  while (counter < length) {
    suffix += chars.charAt(Math.floor(Math.random() * chars.length));
    counter += 1;
  }
  return prefix + suffix;
}

export const albumPrefix = 'E2E Tests: ';

export const createAlbum = async (page: Page, name: string): Promise<string> => {
  await page.goto('/');

  await page.getByText('New album').click();
  const title = withRandomSuffix(`${albumPrefix} ${name} `, 5);
  await page.getByLabel('Title').fill(title);
  await page.getByLabel('Description').fill('Album created by E2E tests.');
  await page.getByText('Save').click();

  await expect(page.getByRole('heading', { level: 1 })).toHaveText(title);
  return title;
}

export const openAlbum = async (page: Page, title: string) => {
  await page.goto('/');
  await page.getByText(title).click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(title);
}

export const getCurrentAlbumKey = (page: Page): string => {
  const keyRegex = /\/albums\/([^/]+)/;
  const url = page.url();

  const match = keyRegex.exec(url);
  expect(match).not.toBeNull();

  return match![1];
}

export const deleteAlbum = async (page: Page, title: string) => {
  await openAlbum(page, title);
  const albumKey = getCurrentAlbumKey(page);

  const response = await page.request.get(`/api/albums/${albumKey}/photos`);
  if (!response.ok()) {
    throw new Error(`Failed to fetch: HTTP ${response.status()}\n\n${await response.text()}`);
  }

  const photos = await response.json();
  for (const photo of photos) {
    await deletePhoto(page, title, photo.title || photo.filename);
  }

  await page.getByText('Delete album').click();
  await page.getByText('Delete', { exact: true }).click();
}

const photoPath = (filename: string): string => path.join(__dirname, '..', 'photos', filename);

export const uploadPhotos = async (page: Page, albumTitle: string, photos: string[]) => {
  await openAlbum(page, albumTitle);

  await page.getByText('Upload photos').click();
  const input = page.getByLabel('Drag and drop photos here or click to open upload dialog.');
  await input.setInputFiles(photos.map(photoPath));

  await expect(page.getByText('Uploading')).toHaveCount(0);
}

export const checkTitlesExist = async (page: Page, titles: string[]) => {
  await Promise.all(titles.map(async (photo) => {
    await expect(page.getByTitle(photo)).toBeVisible();
  }));
}

const openPhoto = async (page: Page, albumTitle: string, title: string) => {
  await openAlbum(page, albumTitle);

  await page.getByTitle(title).click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(title);
};

const deletePhoto = async (page: Page, albumTitle: string, title: string) => {
  await openPhoto(page, albumTitle, title);

  await page.getByText('Delete photo').click();
  await page.getByText('Delete', { exact: true }).click();
}
