import { test } from '@playwright/test';
import { createAlbum, deleteAlbum, deletePhoto, login, uploadPhotos } from './actions';

test('create album and upload photo', async ({ page }) => {
  await login(page);
  const albumTitle = await createAlbum(page);

  const photos = ['bus-stop.jpg'];
  await uploadPhotos(page, albumTitle, photos);

  await Promise.all(photos.map(async (photo) => {
      await deletePhoto(page, albumTitle, photo);
    }));
  await deleteAlbum(page, albumTitle);
});
