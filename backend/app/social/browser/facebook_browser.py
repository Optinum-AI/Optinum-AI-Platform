"""Browser-based adapter for Facebook."""

import asyncio
import logging
import re
from typing import TYPE_CHECKING

from .base_browser import BrowserAdapter

if TYPE_CHECKING:
    from playwright.async_api import Page

log = logging.getLogger(__name__)


class FacebookBrowserAdapter(BrowserAdapter):
    platform = "facebook"
    LOGIN_URL = "https://www.facebook.com/login"
    HOME_INDICATOR = '[role="banner"], [aria-label="Facebook"], div[data-pagelet="Stories"]'

    async def _get_handle(self, page: "Page") -> str:
        try:
            await page.goto("https://www.facebook.com/me", wait_until="domcontentloaded")
            await asyncio.sleep(2)
            h1 = await page.query_selector("h1")
            if h1:
                text = await h1.inner_text()
                return text.strip() if text else "facebook-user"
        except Exception as exc:
            log.debug("[facebook] Could not scrape handle: %s", exc)
        return "facebook-user"

    async def _compose_post(self, page: "Page", text: str) -> str | None:
        await page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # Click "What's on your mind" to open the post composer
        trigger = page.locator(
            '[aria-label*="on your mind"], '
            '[aria-label*="Create a post"], '
            'div[role="button"]:has-text("on your mind")'
        ).first
        await trigger.wait_for(timeout=15000)
        await trigger.click()
        await asyncio.sleep(2)

        # Type into the post editor
        editor = page.locator(
            'div[role="textbox"][contenteditable="true"], '
            'div[aria-label*="on your mind"][contenteditable="true"], '
            'div[data-lexical-editor="true"]'
        ).first
        await editor.wait_for(timeout=10000)
        await editor.click()
        await editor.fill(text)
        await asyncio.sleep(1)

        # Click Post with resilient fallback
        post_btn = page.locator(
            'div[role="dialog"] div[aria-label="Post"][role="button"], '
            'div[role="dialog"] div[aria-label="Post"], '
            'div[aria-label="Post"][role="button"]'
        ).last

        try:
            await post_btn.wait_for(state="visible", timeout=8000)
            await post_btn.click()
        except Exception:
            await page.evaluate("""
                () => {
                    const btns = Array.from(document.querySelectorAll('div[aria-label="Post"], div[role="button"], span'));
                    const postBtn = btns.find(b => 
                        b.getAttribute('aria-label') === 'Post' || 
                        (b.getAttribute('role') === 'button' && b.textContent.trim() === 'Post')
                    );
                    if (postBtn) {
                        postBtn.click();
                    }
                }
            """)
        await asyncio.sleep(3)

        log.info("[facebook] Post submitted via browser")
        return "browser-post"

    async def _compose_media_post(self, page: "Page", text: str, file_path: str) -> str | None:
        await page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        trigger = page.locator(
            '[aria-label*="on your mind"], '
            '[aria-label*="Create a post"], '
            'div[role="button"]:has-text("on your mind")'
        ).first
        await trigger.wait_for(timeout=15000)
        await trigger.click()
        await asyncio.sleep(2)

        # Click Photo/Video button
        photo_btn = page.locator(
            'div[aria-label*="Photo"][role="button"], '
            'span:has-text("Photo/video")'
        ).first
        await photo_btn.click()
        await asyncio.sleep(1)

        file_input = page.locator('input[type="file"][accept*="image"]').first
        await file_input.set_input_files(file_path)
        await asyncio.sleep(3)

        dialogs = page.locator('[role="dialog"]:visible, dialog[open]:visible')
        dialog = dialogs.last
        editor_selector = 'div[role="textbox"][contenteditable="true"]'
        editor = dialog.locator(editor_selector).first
        if not await editor.count():
            editor = page.locator(f'{editor_selector}:visible').last
        await editor.wait_for(state="visible", timeout=10000)
        await editor.click()
        await editor.fill(text)
        await asyncio.sleep(1)

        post_selector = (
            'div[role="dialog"] div[aria-label="Post"][role="button"], '
            'div[role="dialog"] div[aria-label="Post"], '
            'div[aria-label="Post"][role="button"]'
        )
        post_btn = dialog.locator(post_selector).last
        if not await post_btn.count():
            post_btn = page.locator(post_selector).filter(visible=True).last

        try:
            await post_btn.wait_for(state="visible", timeout=8000)
            await post_btn.click()
        except Exception:
            await page.evaluate("""
                () => {
                    const btns = Array.from(document.querySelectorAll('div[aria-label="Post"], div[role="button"]'));
                    const postBtn = btns.find(b => b.getAttribute('aria-label') === 'Post');
                    if (postBtn) postBtn.click();
                }
            """)
        await asyncio.sleep(3)

        log.info("[facebook] Media post submitted via browser")
        return "browser-post"
