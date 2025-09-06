import { expect, test } from '@playwright/test';
import { checkTitlesExist, createAlbum, deleteAlbum, login, uploadPhotos } from './actions';

let albumTitle: string;

test('create album and upload photo', async ({ page }) => {
  await login(page);
  albumTitle = await createAlbum(page, "create and upload");

  // Visibility should be private by default.
  await expect(page.getByText('Private')).toBeVisible();

  await uploadPhotos(page, albumTitle, ['bus-stop.jpg', "tower.jpg"]);
  await checkTitlesExist(page, ['bus-stop.jpg', "tower.jpg"]);

  await uploadPhotos(page, albumTitle, ["tower.jpg", "havfrue.jpg"]);
  await expect(page.getByText('Successfully uploaded 1 photo.')).toBeVisible();
  await expect(page.getByText('Failed to upload tower.jpg. Photo with this filename already exists in the album.')).toBeVisible();
});

test.afterEach(async ({ page }) => {
  await deleteAlbum(page, albumTitle);
});
