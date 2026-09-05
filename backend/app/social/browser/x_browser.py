"""Browser-based adapter for X (Twitter)."""

import asyncio
import logging
from typing import TYPE_CHECKING

from .base_browser import BrowserAdapter

if TYPE_CHECKING:
    from playwright.async_api import Page

log = logging.getLogger(__name__)


class XBrowserAdapter(BrowserAdapter):
    platform = "x"
    LOGIN_URL = "https://x.com/i/flow/login"
    HOME_INDICATOR = '[data-testid="primaryColumn"]'

    async def _get_handle(self, page: "Page") -> str:
        try:
            await page.goto("https://x.com/settings/account", wait_until="domcontentloaded")
            await asyncio.sleep(2)
            el = await page.query_selector('[data-testid="UserName"]')
            if el:
                text = await el.inner_text()
                return text.strip() if text else "x-user"
            link = await page.query_selector('a[href*="/settings"] span')
            if link:
                return await link.inner_text()
        except Exception as exc:
            log.debug("[x] Could not scrape handle: %s", exc)
        return "x-user"

    async def _compose_post(self, page: "Page", text: str) -> str | None:
        await page.goto("https://x.com/compose/post", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # Find the tweet compose box
        editor = page.locator('[data-testid="tweetTextarea_0"]:visible').last
        await editor.wait_for(state="visible", timeout=15000)
        await editor.click()
        await editor.fill(text[:280])
        await asyncio.sleep(1)

        # Click the Post button
        post_btn = page.locator('[data-testid="tweetButton"]').last
        try:
            await post_btn.wait_for(state="visible", timeout=8000)
            await post_btn.click()
        except Exception:
            await page.evaluate("""
                () => {
                    const btn = document.querySelector('[data-testid="tweetButton"]');
                    if (btn) btn.click();
                }
            """)
        await asyncio.sleep(3)

        log.info("[x] Post submitted via browser")
        return "browser-post"

    async def _compose_media_post(self, page: "Page", text: str, file_path: str) -> str | None:
        await page.goto("https://x.com/compose/post", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # Attach media
        file_input = page.locator('input[data-testid="fileInput"]').first
        await file_input.wait_for(state="attached", timeout=15000)
        await file_input.set_input_files(file_path)
        await asyncio.sleep(3)

        editor = page.locator('[data-testid="tweetTextarea_0"]:visible').last
        await editor.wait_for(state="visible", timeout=15000)
        await editor.click()
        await editor.fill(text[:280])
        await asyncio.sleep(1)

        post_btn = page.locator('[data-testid="tweetButton"]').last
        try:
            await post_btn.click()
        except Exception:
            await page.evaluate("""
                () => {
                    const btn = document.querySelector('[data-testid="tweetButton"]');
                    if (btn) btn.click();
                }
            """)
        await asyncio.sleep(3)

        log.info("[x] Media post submitted via browser")
        return "browser-post"
