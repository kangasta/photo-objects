import { expect, test } from '@playwright/test';
import { createAlbumAndUploadPhotos, deleteAlbum, getCurrentAlbumKey, listPhotos, login, openAlbum, withRandomSuffix } from './actions';

test('review photo change requests', async ({ context, page }, testInfo) => {
  await login(page);
  const altText = withRandomSuffix('Test alt text ', 5);
  const tag = withRandomSuffix('test-', 5);

  const photos = ['bus-stop.jpg', "tower.jpg", "havfrue.jpg"];
  const albumTitle = await createAlbumAndUploadPhotos(page, testInfo, "photo change requests", photos);

  const albumKey = getCurrentAlbumKey(page);
  const cookies = await context.cookies();
  const csrftoken = cookies.find(c => c.name === 'csrftoken')?.value ?? '';
  await Promise.all(photos.map(async (photo) => {
    const response = await page.request.post(`/api/albums/${albumKey}/photos/${photo}/change-requests`, {
      data: {
        alt_text: altText,
        tags: [tag, 'test-automation'],
      },
      headers: {
        'X-CSRFToken': csrftoken,
      },
    });
    expect(response.ok(), `Error response: ${await response.text()}`).toBe(true);
  }));

  await page.getByTitle('Logged in as admin').click();
  await page.getByText('Review photo change requests').click();

  const tagsString = `${tag}, test-automation`;

  // Approve the first and second review
  expect(page.getByText('There are 3 change requests in the review queue.')).toHaveCount(1, { timeout: 5000 });
  expect(await page.getByLabel('Tags').inputValue()).toBe(tagsString);
  await page.getByText('Save').click();
  expect(page.getByText('There are 2 change requests in the review queue.')).toHaveCount(1, { timeout: 5000 });
  expect(await page.getByLabel('Tags').inputValue()).toBe(tagsString);
  await page.getByText('Save').click();

  // Reject the third review
  expect(page.getByText('This is the last change request in the review queue.')).toHaveCount(1, { timeout: 5000 });
  expect(await page.getByLabel('Tags').inputValue()).toBe(tagsString);
  await page.getByLabel('Action').selectOption('Reject');
  await page.getByText('Save').click();

  await openAlbum(page, albumTitle);
  expect(page.getByAltText(altText)).toHaveCount(2, { timeout: 5000 });

  await listPhotos(page);
  expect(page.getByAltText(altText)).toHaveCount(2, { timeout: 5000 });

  await listPhotos(page, tag);
  expect(page.getByAltText(altText)).toHaveCount(2, { timeout: 5000 });
});

test.afterEach(async ({ page }, testInfo) => {
  await deleteAlbum(page, testInfo);
});
