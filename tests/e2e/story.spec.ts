import { expect, test } from '@playwright/test';
import { addPhotoToStory, createAlbumAndUploadPhotos, createStory, deleteAlbums, deleteStories, login, openStory } from './actions';

test('create story and add photo references', async ({ page }, testInfo) => {
    await login(page);
    const albumATitle = await createAlbumAndUploadPhotos(page, testInfo, "use stories A", ['bus-stop.jpg', "tower.jpg"], "Hidden");
    const albumBTitle = await createAlbumAndUploadPhotos(page, testInfo, "use stories B", ['havfrue.jpg']);

    const storyTitle = await createStory(page, testInfo, "use stories", "Hidden");

    await addPhotoToStory(page, storyTitle, albumATitle, 'bus-stop.jpg');
    await addPhotoToStory(page, storyTitle, albumBTitle, 'havfrue.jpg');

    await openStory(page, storyTitle);
    await expect(page.getByTitle('bus-stop.jpg')).toBeVisible();
    await expect(page.getByTitle('tower.jpg')).not.toBeVisible();
    await expect(page.getByTitle('havfrue.jpg')).toBeVisible();

    // Check that photo view has a link to the album
    page.getByTitle('havfrue.jpg').click();
    await expect(page.getByText(albumBTitle)).toBeVisible();
    await expect(page.getByText(albumATitle)).not.toBeVisible();

    // Add title to the currently open photo reference
    await page.getByText('Edit reference').click();
    await page.getByLabel('Title').fill('The Little Mermaid');
    await page.getByText('Save').click();

    await openStory(page, storyTitle);
    await expect(page.getByTitle('havfrue.jpg')).not.toBeVisible();
    await expect(page.getByTitle('The Little Mermaid')).toBeVisible();

    // Logout and check there is only one photo visible in the story
    await page.getByTitle('Logged in as admin').click();
    await page.getByText('Logout').click();

    await expect(page.getByTitle('The Little Mermaid')).not.toBeVisible();
    await expect(page.getByTitle('bus-stop.jpg')).toBeVisible();

    // Login and remove one of the photo references from the story
    await login(page);
    await openStory(page, storyTitle);

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
