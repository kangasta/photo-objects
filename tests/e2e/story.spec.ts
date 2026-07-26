import { expect, test } from '@playwright/test';
import { addPhotoToStory, createAlbumAndUploadPhotos, createStory, deleteAlbums, deleteStories, login, openStory } from './actions';

test('create story and add photo references', async ({ page }, testInfo) => {
    await login(page);
    const albumATitle = await createAlbumAndUploadPhotos(page, testInfo, "use stories A", ['bus-stop.jpg', "tower.jpg"]);
    const albumBTitle = await createAlbumAndUploadPhotos(page, testInfo, "use stories B", ['havfrue.jpg']);

    const storyTitle = await createStory(page, testInfo, "use stories");

    await addPhotoToStory(page, storyTitle, albumATitle, 'bus-stop.jpg');
    await addPhotoToStory(page, storyTitle, albumBTitle, 'havfrue.jpg');

    await openStory(page, storyTitle);
    await expect(page.getByTitle('bus-stop.jpg')).toBeVisible();
    await expect(page.getByTitle('tower.jpg')).not.toBeVisible();
    await expect(page.getByTitle('havfrue.jpg')).toBeVisible();

    // Add title to one of the photo references
    await page.getByTitle('havfrue.jpg').click();
    await page.getByText('Edit reference').click();
    await page.getByLabel('Title').fill('The Little Mermaid');
    await page.getByText('Save').click();

    await openStory(page, storyTitle);
    await expect(page.getByTitle('havfrue.jpg')).not.toBeVisible();
    await expect(page.getByTitle('The Little Mermaid')).toBeVisible();

    // Remove one of the photo references from the story
    await page.getByTitle('bus-stop.jpg').click();
    await page.getByText('Remove from story').click();
    await page.getByText('Delete', { exact: true }).click();

    await openStory(page, storyTitle);
    await expect(page.getByTitle('bus-stop.jpg')).not.toBeVisible();
});

test.afterEach(async ({ page }, testInfo) => {
    await deleteStories(page, testInfo);
    await deleteAlbums(page, testInfo);
});
