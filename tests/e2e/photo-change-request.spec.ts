import { expect, test } from '@playwright/test';
import { checkTitlesExist, createAlbum, deleteAlbum, getCurrentAlbumKey, login, openAlbum, uploadPhotos } from './actions';

let albumTitle: string;


test('review photo change requests', async ({ context, page }) => {
  await login(page);
  albumTitle = await createAlbum(page, "photo change requests");
  const albumKey = getCurrentAlbumKey(page);

  const photos = ['bus-stop.jpg', "tower.jpg", "havfrue.jpg"];
  await uploadPhotos(page, albumTitle, photos);

  const cookies = await context.cookies();
  const csrftoken = cookies.find(c => c.name === 'csrftoken')?.value ?? '';
  await Promise.all(photos.map(async (photo) => {
    const response = await page.request.post(`/api/albums/${albumKey}/photos/${photo}/change-requests`, {
      data: {
        alt_text: `Test alt text`,
      },
      headers: {
        'X-CSRFToken': csrftoken,
      },
    });
    expect(response.ok(), `Error response: ${await response.text()}`).toBe(true);
  }));

  await page.getByTitle('Logged in as admin').click();
  await page.getByText('Review photo change requests').click();

  // Approve the first and second review
  expect(page.getByText('There are 3 change requests in the review queue.')).toBeVisible();
  await page.getByText('Save').click();
  expect(page.getByText('There are 2 change requests in the review queue.')).toBeVisible();
  await page.getByText('Save').click();
  
  // Reject the third review
  expect(page.getByText('This is the last change request in the review queue.')).toBeVisible();
  await page.getByLabel('Action').selectOption('Reject');
  await page.getByText('Save').click();

  await openAlbum(page, albumTitle);
  expect(page.getByAltText('Test alt text', { })).toHaveCount(2);
});

test.afterEach(async ({ page }) => {
  await deleteAlbum(page, albumTitle);
});
