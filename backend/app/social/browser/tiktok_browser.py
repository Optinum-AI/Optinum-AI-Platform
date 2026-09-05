"""Browser-based adapter for TikTok."""

import asyncio
import logging
from typing import TYPE_CHECKING

from .base_browser import BrowserAdapter

if TYPE_CHECKING:
    from playwright.async_api import Page

log = logging.getLogger(__name__)


class TikTokBrowserAdapter(BrowserAdapter):
    platform = "tiktok"
    LOGIN_URL = "https://www.tiktok.com/login/phone-or-email/email"
    HOME_INDICATOR = '[data-e2e="nav-foryou"], a[href="/foryou"]'

    async def _get_handle(self, page: "Page") -> str:
        try:
            await page.goto("https://www.tiktok.com/setting", wait_until="domcontentloaded")
            await asyncio.sleep(3)
            el = await page.query_selector('[data-e2e="username-value"], .username')
            if el:
                text = await el.inner_text()
                return f"@{text.strip()}" if text else "tiktok-user"
        except Exception as exc:
            log.debug("[tiktok] Could not scrape handle: %s", exc)
        return "tiktok-user"

    async def _compose_post(self, page: "Page", text: str) -> str | None:
        raise RuntimeError(
            "TikTok requires a video file for publishing. Use publish_media instead."
        )

    async def _compose_media_post(self, page: "Page", text: str, file_path: str) -> str | None:
        await page.goto("https://www.tiktok.com/creator#/upload?scene=creator_center",
                        wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Upload file
        file_input = page.locator('input[type="file"][accept*="video"]').first
        await file_input.set_input_files(file_path)
        await asyncio.sleep(5)

        # Wait for upload to process
        await asyncio.sleep(10)

        # Fill caption
        caption = page.locator(
            'div[contenteditable="true"][data-placeholder], '
            '.caption-editor div[contenteditable="true"], '
            'div[aria-label*="caption"]'
        ).filter(visible=True).last
        await caption.wait_for(state="visible", timeout=15000)
        await caption.click()
        await caption.fill(text[:2200])
        await asyncio.sleep(1)

        # Click Post
        post_btn = page.locator(
            'button:has-text("Post"), '
            'div[role="button"]:has-text("Post")'
        ).filter(visible=True).last
        await post_btn.wait_for(state="visible", timeout=10000)
        await post_btn.click()
        await asyncio.sleep(5)

        log.info("[tiktok] Video uploaded via browser")
        return "browser-post"
