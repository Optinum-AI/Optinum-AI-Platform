"""Browser-based adapter for LinkedIn."""

import asyncio
import logging
import re
from typing import TYPE_CHECKING

from .base_browser import BrowserAdapter

if TYPE_CHECKING:
    from playwright.async_api import Page

log = logging.getLogger(__name__)


class LinkedInBrowserAdapter(BrowserAdapter):
    platform = "linkedin"
    LOGIN_URL = "https://www.linkedin.com/login"
    HOME_INDICATOR = '.feed-identity-module, [data-test-id="feed-nav"], .global-nav'

    async def _ensure_authenticated(self, page: "Page") -> None:
        """Validate the saved session using LinkedIn's current rendered DOM."""
        await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        try:
            await page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            await page.wait_for_timeout(750)

        html = (await page.content()).lower()
        current_url = page.url.lower()
        login_markers = (
            "/login",
            "join linkedin",
            "sign in",
            "session_key",
            "checkpoint",
            "challenge",
        )
        if any(marker in current_url for marker in login_markers) or any(
            marker in html for marker in ("sign in to linkedin", "join linkedin", "verify your identity")
        ):
            raise RuntimeError(
                "Authentication required for linkedin; the saved browser session is expired or LinkedIn requested login"
            )

        # Parse the complete rendered document before selecting controls. LinkedIn
        # frequently changes class names while keeping roles, labels, and text.
        has_feed = (await page.locator("main").first.count()) > 0
        has_share_entry = (await page.get_by_text(
            re.compile(r"^Start a post$", re.I)
        ).first.count()) > 0
        has_nav = (await page.locator(
            'nav, a[href*="/feed"], button[aria-label*="Me"], [data-test-id*="feed"]'
        ).first.count()) > 0
        if not has_feed or not (has_share_entry or has_nav):
            raise RuntimeError(
                "Authentication required for linkedin; authenticated feed controls were not present in the rendered page"
            )

    async def _get_handle(self, page: "Page") -> str:
        try:
            await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
            await asyncio.sleep(2)
            el = await page.query_selector('.feed-identity-module__actor-meta a, .profile-rail-card__actor-link')
            if el:
                text = await el.inner_text()
                return text.strip() if text else "linkedin-user"
        except Exception as exc:
            log.debug("[linkedin] Could not scrape handle: %s", exc)
        return "linkedin-user"

    async def _compose_post(self, page: "Page", text: str) -> str | None:
        await self._wait_for_feed(page)
        await self._dismiss_overlays(page)
        start_post = await self._start_post_control(page)
        try:
            await start_post.scroll_into_view_if_needed()
            await start_post.wait_for(state="visible", timeout=15000)
            await start_post.click(trial=True, timeout=5000)
            await start_post.click(timeout=10000)
            await self._wait_for_composer(page)
        except Exception as exc:
            await self._capture_failure(page, start_post, str(exc))
            raise RuntimeError(
                "LinkedIn sharing composer could not be opened. "
                f"The Start a post control was unavailable or blocked: {exc}"
            ) from exc

        # Fill the text editor
        editor = page.locator(
            'div[role="textbox"][contenteditable="true"], '
            '.ql-editor[contenteditable="true"], div[contenteditable="true"]'
        ).first
        await editor.wait_for(state="visible", timeout=10000)
        await editor.click()
        await editor.fill(text)
        await page.wait_for_timeout(500)

        # Click Post button
        post_btn = page.get_by_role("button", name=re.compile(r"^Post$", re.I)).last
        await post_btn.wait_for(state="visible", timeout=10000)
        await post_btn.click()
        await page.wait_for_timeout(2500)

        log.info("[linkedin] Post submitted via browser")
        return "browser-post"

    async def _wait_for_feed(self, page: "Page") -> None:
        try:
            await page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            await page.wait_for_timeout(750)
        await page.locator("main").first.wait_for(state="visible", timeout=15000)

    async def _dismiss_overlays(self, page: "Page") -> None:
        for name in ("Dismiss", "Close", "Not now"):
            control = page.get_by_role("button", name=re.compile(rf"^{name}$", re.I)).first
            if await control.count() and await control.is_visible():
                await control.click(timeout=3000)
                await page.wait_for_timeout(300)

    async def _start_post_control(self, page: "Page"):
        selectors = (
            'button[aria-label="Start a post"]',
            'div[role="button"][aria-label="Start a post"]',
            'button.share-box-feed-entry__trigger',
        )
        control = page.locator(", ".join(selectors)).first
        if await control.count():
            return control
        text = page.get_by_text(re.compile(r"^Start a post$", re.I)).first
        if await text.count():
            parent = text.locator("xpath=ancestor::*[@role='button' or self::button][1]")
            if await parent.count():
                return parent
        raise RuntimeError("LinkedIn Start a post control was not found on the feed")

    async def _wait_for_composer(self, page: "Page") -> None:
        await page.locator(
            'div[role="textbox"][contenteditable="true"], '
            '.ql-editor[contenteditable="true"]'
        ).first.wait_for(state="visible", timeout=10000)

    async def _capture_failure(self, page: "Page", control, error: str) -> None:
        path = f"/tmp/optinum-linkedin-share-{int(asyncio.get_running_loop().time())}.png"
        try:
            await page.screenshot(path=path, full_page=True)
            info = await control.evaluate(
                "(el) => ({tag: el.tagName, role: el.getAttribute('role'), "
                "label: el.getAttribute('aria-label'), outer: el.outerHTML.slice(0, 500)})"
            )
            log.error(
                "[linkedin] Share composer failed: error=%s control=%s screenshot=%s",
                error, info, path,
            )
        except Exception as capture_error:
            log.error("[linkedin] Share composer failed: %s; diagnostic capture failed: %s", error, capture_error)

    async def _compose_media_post(self, page: "Page", text: str, file_path: str) -> str | None:
        await self._wait_for_feed(page)
        await self._dismiss_overlays(page)
        start_post = await self._start_post_control(page)
        try:
            await start_post.scroll_into_view_if_needed()
            await start_post.wait_for(state="visible", timeout=15000)
            await start_post.click(trial=True, timeout=5000)
            await start_post.click(timeout=10000)
            await self._wait_for_composer(page)
        except Exception as exc:
            await self._capture_failure(page, start_post, str(exc))
            raise RuntimeError(
                "LinkedIn sharing composer could not be opened for media. "
                f"The Start a post control was unavailable or blocked: {exc}"
            ) from exc

        # Click media/photo button and upload
        media_btn = page.get_by_role(
            "button", name=re.compile(r"(photo|video|media|attachment)", re.I)
        ).first
        await media_btn.wait_for(state="visible", timeout=10000)
        await media_btn.click()
        await page.wait_for_timeout(500)

        file_input = page.locator('input[type="file"]').first
        await file_input.wait_for(state="attached", timeout=10000)
        await file_input.set_input_files(file_path)
        await page.wait_for_timeout(1500)

        # LinkedIn first shows an image-preview dialog above the composer.
        # Advance it before touching the caption editor; otherwise the preview
        # layer intercepts pointer events even though the editor is visible.
        preview_dialogs = page.locator('dialog[open]:visible, [role="dialog"]:visible')
        for index in range(await preview_dialogs.count()):
            candidate = preview_dialogs.nth(index)
            next_button = candidate.get_by_role("button", name=re.compile(r"^Next$", re.I)).last
            if await next_button.count() and await next_button.is_visible():
                await next_button.click(timeout=10000)
                await page.wait_for_timeout(750)
                break

        # LinkedIn moves the composer into an open media dialog after upload.
        # Scope editor and submit controls to that dialog so the background
        # feed editor cannot intercept pointer events.
        editor_selector = (
            'div[role="textbox"][contenteditable="true"], '
            '.ql-editor[contenteditable="true"], div[contenteditable="true"]'
        )
        dialogs = page.locator('dialog[open]:visible, [role="dialog"]:visible')
        dialog = None
        for index in range(await dialogs.count()):
            candidate = dialogs.nth(index)
            if await candidate.locator(editor_selector).count():
                dialog = candidate
                break
        editor = (
            dialog.locator(editor_selector).first
            if dialog is not None
            else page.locator(f'{editor_selector}:visible').last
        )
        await editor.wait_for(state="visible", timeout=10000)
        await editor.click()
        await editor.fill(text)
        await page.wait_for_timeout(500)

        post_btn = (
            dialog.get_by_role("button", name=re.compile(r"^Post$", re.I)).last
            if dialog is not None
            else page.get_by_role("button", name=re.compile(r"^Post$", re.I)).last
        )
        await post_btn.wait_for(state="visible", timeout=10000)
        await post_btn.click()
        await page.wait_for_timeout(2500)

        log.info("[linkedin] Media post submitted via browser")
        return "browser-post"
