"""Browser-based adapter for Instagram."""

import asyncio
import logging
import re
from typing import TYPE_CHECKING

from .base_browser import BrowserAdapter

if TYPE_CHECKING:
    from playwright.async_api import Page

log = logging.getLogger(__name__)


class InstagramBrowserAdapter(BrowserAdapter):
    platform = "instagram"
    LOGIN_URL = "https://www.instagram.com/accounts/login/"
    HOME_INDICATOR = 'svg[aria-label="Home"], a[href="/"][role="link"] svg'

    async def _get_handle(self, page: "Page") -> str:
        try:
            await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            await asyncio.sleep(2)
            # Try to find profile link in nav
            profile_link = await page.query_selector('a[href*="/"][role="link"] img[alt]')
            if profile_link:
                alt = await profile_link.get_attribute("alt")
                if alt and "profile" in alt.lower():
                    return f"@{alt.split(chr(39))[0].strip()}"  # Extract name from alt
            # Fallback: navigate to accounts/edit
            await page.goto("https://www.instagram.com/accounts/edit/", wait_until="domcontentloaded")
            await asyncio.sleep(2)
            username_input = await page.query_selector('input[name="username"]')
            if username_input:
                val = await username_input.input_value()
                return f"@{val}" if val else "instagram-user"
        except Exception as exc:
            log.debug("[instagram] Could not scrape handle: %s", exc)
        return "instagram-user"

    async def _compose_post(self, page: "Page", text: str) -> str | None:
        # Instagram web doesn't support text-only posts
        raise RuntimeError(
            "Instagram requires an image or video. Use publish_media instead."
        )

    async def _compose_media_post(self, page: "Page", text: str, file_path: str) -> str | None:
        await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            # Instagram can keep analytics requests open; DOM readiness is sufficient.
            await page.wait_for_timeout(500)
        await self._dismiss_known_overlays(page)

        create_btn = await self._new_post_control(page)
        last_error = ""
        for attempt in range(2):
            try:
                await create_btn.scroll_into_view_if_needed()
                await create_btn.wait_for(state="visible", timeout=10000)
                # trial=True reports pointer interception without mutating the page.
                await create_btn.click(trial=True, timeout=5000)
                await create_btn.click(timeout=10000)
                await self._wait_for_create_post(page)
                break
            except Exception as exc:
                last_error = str(exc)
                if attempt == 0:
                    await self._dismiss_known_overlays(page)
                    await page.wait_for_timeout(750)
                    create_btn = await self._new_post_control(page)
                    continue
                await self._capture_click_failure(page, create_btn, last_error)
                raise RuntimeError(
                    "Instagram New Post click was blocked after 2 attempts. "
                    f"Pointer/UI diagnostic: {last_error}"
                ) from exc

        # Upload file
        file_input = page.locator('input[type="file"]:visible').first
        if not await file_input.count():
            file_input = page.locator('input[type="file"]').first
        await file_input.wait_for(state="attached", timeout=15000)
        await file_input.set_input_files(file_path)
        await page.wait_for_timeout(1500)

        # Click Next (crop step)
        next_btn = page.locator(
            'button:has-text("Next"), div[role="button"]:has-text("Next")'
        ).filter(visible=True).last
        await next_btn.click()
        await asyncio.sleep(2)

        # Click Next again (filter step)
        next_btn2 = page.locator(
            'button:has-text("Next"), div[role="button"]:has-text("Next")'
        ).filter(visible=True).last
        await next_btn2.click()
        await asyncio.sleep(2)

        # Add caption
        caption = page.locator(
            'textarea[aria-label*="caption"], textarea[aria-label*="Write a caption"]'
        ).filter(visible=True).last
        await caption.fill(text)
        await asyncio.sleep(1)

        # Share
        share_btn = page.locator(
            'button:has-text("Share"), div[role="button"]:has-text("Share")'
        ).filter(visible=True).last
        await share_btn.click()
        await asyncio.sleep(5)

        log.info("[instagram] Media post submitted via browser")
        return "browser-post"

    async def _dismiss_known_overlays(self, page: "Page") -> None:
        for label in ("Not now", "Close", "Cancel"):
            button = page.get_by_role("button", name=re.compile(rf"^{re.escape(label)}$", re.I)).first
            if await button.count() and await button.is_visible():
                await button.click(timeout=3000)
                await page.wait_for_timeout(300)

    async def _new_post_control(self, page: "Page"):
        semantic = page.get_by_role("button", name=re.compile(r"new post", re.I)).first
        if await semantic.count():
            return semantic
        link = page.locator('a[href="/create/"], a[href^="/create/"]').first
        if await link.count():
            return link
        icon = page.locator('svg[aria-label="New post"], svg[aria-label="New Post"]').first
        if not await icon.count():
            raise RuntimeError("Instagram New Post control was not found")
        parent = icon.locator("xpath=ancestor::*[@role='button' or @role='link'][1]")
        return parent if await parent.count() else icon.locator("xpath=..")

    async def _wait_for_create_post(self, page: "Page") -> None:
        await page.locator('input[type="file"]').first.wait_for(state="attached", timeout=10000)
        dialog = page.get_by_role("dialog").filter(has_text=re.compile(r"create new post", re.I))
        heading = page.get_by_text(re.compile(r"create new post", re.I)).first
        if (await dialog.count() and await dialog.first.is_visible()) or (
            await heading.count() and await heading.is_visible()
        ) or "/create/" in page.url:
            return
        raise RuntimeError("Instagram New Post click did not open the Create Post interface")

    async def _capture_click_failure(self, page: "Page", control, error: str) -> None:
        path = f"/tmp/optinum-instagram-new-post-{int(asyncio.get_running_loop().time())}.png"
        try:
            await page.screenshot(path=path, full_page=True)
            element_info = await control.evaluate(
                "(el) => ({tag: el.tagName, role: el.getAttribute('role'), "
                "label: el.getAttribute('aria-label'), outer: el.outerHTML.slice(0, 500)})"
            )
            log.error(
                "[instagram] New Post click failed: error=%s control=%s screenshot=%s",
                error,
                element_info,
                path,
            )
        except Exception as capture_error:
            log.error(
                "[instagram] New Post click failed: error=%s; diagnostic capture failed: %s",
                error,
                capture_error,
            )
