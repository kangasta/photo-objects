import { expect, test } from '@playwright/test';
import { createAlbum, deleteAlbum, login, uploadPhotos } from './actions';

let albumTitle: string;

test('create album and upload photo', async ({ page }) => {
  await login(page);
  albumTitle = await createAlbum(page);

  // Visibility should be private by default.
  await expect(page.getByText('Private')).toBeVisible();

  await uploadPhotos(page, albumTitle, ['bus-stop.jpg', "tower.jpg"]);
});

test.afterEach(async ({ page }) => {
  await deleteAlbum(page, albumTitle);
});
