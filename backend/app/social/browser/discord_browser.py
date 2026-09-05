"""Browser-based adapter for Discord."""

import asyncio
import logging
from typing import TYPE_CHECKING

from .base_browser import BrowserAdapter

if TYPE_CHECKING:
    from playwright.async_api import Page

log = logging.getLogger(__name__)


class DiscordBrowserAdapter(BrowserAdapter):
    platform = "discord"
    LOGIN_URL = "https://discord.com/login"
    HOME_INDICATOR = '[class*="sidebar"], [aria-label="Servers sidebar"]'

    async def _get_handle(self, page: "Page") -> str:
        try:
            await page.goto("https://discord.com/channels/@me", wait_until="domcontentloaded")
            await asyncio.sleep(3)
            el = await page.query_selector('[class*="panelTitleContainer"] [class*="title"]')
            if el:
                text = await el.inner_text()
                return text.strip() if text else "discord-user"
        except Exception as exc:
            log.debug("[discord] Could not scrape handle: %s", exc)
        return "discord-user"

    async def _compose_post(self, page: "Page", text: str) -> str | None:
        # Discord browser adapter sends to the first visible channel
        await page.goto("https://discord.com/channels/@me", wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Find the message input
        editor = page.locator(
            'div[role="textbox"][contenteditable="true"], '
            'div[data-slate-editor="true"]'
        ).first
        await editor.wait_for(timeout=15000)
        await editor.click()
        await editor.fill(text)
        await asyncio.sleep(0.5)

        # Press Enter to send
        await editor.press("Enter")
        await asyncio.sleep(2)

        log.info("[discord] Message sent via browser")
        return "browser-post"

    async def _compose_media_post(self, page: "Page", text: str, file_path: str) -> str | None:
        await page.goto("https://discord.com/channels/@me", wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Click the upload/attach button
        attach_btn = page.locator('button[aria-label*="Upload"], button[aria-label*="Attach"]').first
        await attach_btn.click()
        await asyncio.sleep(1)

        file_input = page.locator('input[type="file"]').first
        await file_input.set_input_files(file_path)
        await asyncio.sleep(3)

        # Add text to the message
        editor = page.locator(
            'div[role="textbox"][contenteditable="true"]'
        ).filter(visible=True).last
        await editor.wait_for(state="visible", timeout=10000)
        await editor.click()
        await editor.fill(text)
        await asyncio.sleep(0.5)

        await editor.press("Enter")
        await asyncio.sleep(2)

        log.info("[discord] Media message sent via browser")
        return "browser-post"
