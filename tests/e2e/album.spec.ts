import { expect, test } from '@playwright/test';
import { checkTitlesExist, createAlbumAndUploadPhotos, deleteAlbum, login, uploadPhotos, withRandomSuffix } from './actions';

test('create album and upload photo', async ({ page }, testInfo) => {
  await login(page);
  const albumTitle = await createAlbumAndUploadPhotos(page, testInfo, "create and upload", ['bus-stop.jpg', "tower.jpg"]);
  
  // Visibility should be private by default.
  await expect(page.getByText('Private')).toBeVisible();

  await checkTitlesExist(page, ['bus-stop.jpg', "tower.jpg"]);

  await uploadPhotos(page, albumTitle, ["tower.jpg", "havfrue.jpg"]);
  await expect(page.getByText('Ready', { exact: true })).toHaveCount(1);
  await expect(page.getByText('Failed', { exact: true })).toHaveCount(1);
  await expect(page.getByText('Failed to upload tower.jpg: Photo with this filename already exists in the album.')).toBeVisible();

  await page.getByText('Done', { exact: true }).click();
});

test('modify photo and list photos by tag', async ({ page }, testInfo) => {
  await login(page);
  await createAlbumAndUploadPhotos(page, testInfo, "use tags", ['bus-stop.jpg', "tower.jpg"]);

  // Go to edit photo form
  await page.getByTitle('bus-stop.jpg').click();
  await page.getByText('Edit photo' ).click();

  // Add tags and save
  const testTag = withRandomSuffix('test-tag-', 5);
  await page.getByLabel('Tags').fill(`Paris, France, ${testTag}`);
  await page.getByRole('button', { name: 'Save' }).click();

  // List photos by tag and check that the photo is visible there
  await page.getByText(testTag).click();
  expect(page.getByText('Photos')).toBeVisible();
  await expect(page.getByTitle('bus-stop.jpg')).toBeVisible();
  await expect(page.getByTitle('tower.jpg')).not.toBeVisible();
});

test.afterEach(async ({ page }, testInfo) => {
  await deleteAlbum(page, testInfo);
});
