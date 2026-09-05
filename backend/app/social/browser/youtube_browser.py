"""Browser-based adapter for YouTube."""

import asyncio
import logging
from typing import TYPE_CHECKING

from .base_browser import BrowserAdapter

if TYPE_CHECKING:
    from playwright.async_api import Page

log = logging.getLogger(__name__)


class YouTubeBrowserAdapter(BrowserAdapter):
    platform = "youtube"
    LOGIN_URL = "https://accounts.google.com/ServiceLogin?service=youtube"
    HOME_INDICATOR = 'ytd-masthead, #avatar-btn, button#avatar-btn'

    async def _get_handle(self, page: "Page") -> str:
        try:
            await page.goto("https://studio.youtube.com/", wait_until="domcontentloaded")
            await asyncio.sleep(3)
            el = await page.query_selector('#channel-title, .channel-name')
            if el:
                text = await el.inner_text()
                return text.strip() if text else "youtube-channel"
        except Exception as exc:
            log.debug("[youtube] Could not scrape handle: %s", exc)
        return "youtube-channel"

    async def _compose_post(self, page: "Page", text: str) -> str | None:
        # YouTube doesn't support text-only posts via web
        raise RuntimeError(
            "YouTube requires a video file for publishing. Use publish_media instead."
        )

    async def _compose_media_post(self, page: "Page", text: str, file_path: str) -> str | None:
        await page.goto("https://studio.youtube.com/", wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Click upload/create button
        create_btn = page.locator(
            '#create-icon, button[aria-label="Create"], #upload-icon'
        ).filter(visible=True).last
        await create_btn.wait_for(timeout=15000)
        await create_btn.click()
        await asyncio.sleep(1)

        upload_opt = page.locator(
            'tp-yt-paper-item:has-text("Upload video"), #text-item-0'
        ).filter(visible=True).last
        await upload_opt.click()
        await asyncio.sleep(2)

        # Upload file
        file_input = page.locator('input[type="file"]').first
        await file_input.set_input_files(file_path)
        await asyncio.sleep(5)

        # Fill title
        title_input = page.locator(
            '#textbox[aria-label*="title"], #title-textarea div[contenteditable]'
        ).filter(visible=True).last
        await title_input.wait_for(timeout=15000)
        await title_input.click()
        await title_input.fill(text[:100])
        await asyncio.sleep(1)

        # Fill description
        desc_input = page.locator(
            '#textbox[aria-label*="description"], #description-textarea div[contenteditable]'
        ).filter(visible=True).last
        await desc_input.click()
        await desc_input.fill(text)
        await asyncio.sleep(1)

        # Click through Next buttons to reach visibility
        for _ in range(3):
            next_btn = page.locator(
                '#next-button, button:has-text("Next")'
            ).filter(visible=True).last
            await next_btn.click()
            await asyncio.sleep(2)

        # Set to Public
        public_radio = page.locator(
            'tp-yt-paper-radio-button[name="PUBLIC"], '
            '#privacy-radios tp-yt-paper-radio-button:first-child'
        ).filter(visible=True).last
        await public_radio.click()
        await asyncio.sleep(1)

        # Publish
        publish_btn = page.locator(
            '#done-button, button:has-text("Publish")'
        ).filter(visible=True).last
        await publish_btn.click()
        await asyncio.sleep(5)

        log.info("[youtube] Video uploaded via browser")
        return "browser-post"
