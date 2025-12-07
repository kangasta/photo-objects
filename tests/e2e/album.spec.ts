import { expect, test } from '@playwright/test';
import { checkTitlesExist, createAlbum, deleteAlbum, login, uploadPhotos } from './actions';

let albumTitle: string;

test('create album and upload photo', async ({ page }) => {
  await login(page);
  albumTitle = await createAlbum(page, "create and upload");

  // Visibility should be private by default.
  await expect(page.getByText('Private')).toBeVisible();

  await uploadPhotos(page, albumTitle, ['bus-stop.jpg', "tower.jpg"]);
  await expect(page.getByText('Ready', { exact: true })).toHaveCount(2);
  await page.getByText('Done', { exact: true }).click();
  await checkTitlesExist(page, ['bus-stop.jpg', "tower.jpg"]);

  await uploadPhotos(page, albumTitle, ["tower.jpg", "havfrue.jpg"]);
  await expect(page.getByText('Ready', { exact: true })).toHaveCount(1);
  await expect(page.getByText('Failed', { exact: true })).toHaveCount(1);
  await expect(page.getByText('Failed to upload tower.jpg: Photo with this filename already exists in the album.')).toBeVisible();

  await page.getByText('Done', { exact: true }).click();
});

test.afterEach(async ({ page }) => {
  await deleteAlbum(page, albumTitle);
});
