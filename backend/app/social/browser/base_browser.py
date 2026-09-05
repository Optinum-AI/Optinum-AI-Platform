"""
Base class for browser-based social-media adapters.

Extends SocialAdapter so it can be used as a drop-in replacement when API
credentials are unavailable.  Playwright is used to drive a real browser:

  • Login  — headed browser; user logs in manually (CAPTCHA / MFA handled by user)
  • Publish — headless browser reuses the saved session cookies
  • No passwords are ever stored
"""

from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from ..base import SocialAdapter
from . import session_store

if TYPE_CHECKING:
    from playwright.async_api import Page, BrowserContext

log = logging.getLogger(__name__)

# How long to wait for the user to finish logging in (seconds)
LOGIN_TIMEOUT_S = 300  # 5 minutes


class BrowserAdapter(SocialAdapter):
    """
    Abstract base for browser-automation adapters.

    Subclasses override:
        LOGIN_URL       — platform login page
        HOME_INDICATOR  — CSS selector present only when logged in
        _get_handle(page)       — scrape the username from the logged-in page
        _compose_post(page, text) — automate posting
    """

    LOGIN_URL: str = ""
    HOME_INDICATOR: str = ""
    platform: str = ""

    # ------------------------------------------------------------------
    # SocialAdapter interface — OAuth methods are not applicable
    # ------------------------------------------------------------------

    def auth_url(self, state: str, redirect_uri: str) -> str:
        raise RuntimeError(
            f"{self.platform} browser adapter does not use OAuth redirect. "
            "Use the /social-hub/{platform}/browser/launch endpoint instead."
        )

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        raise RuntimeError(
            f"{self.platform} browser adapter does not use OAuth code exchange."
        )

    def configured(self) -> bool:
        """Browser adapters are always 'available' — no API keys needed."""
        return True

    # ------------------------------------------------------------------
    # Browser lifecycle helpers
    # ------------------------------------------------------------------

    async def _new_context(
        self,
        playwright,
        headless: bool = True,
        state: dict | None = None,
    ) -> "BrowserContext":
        launch_kwargs = {"headless": headless}
        if Path("/usr/bin/google-chrome").exists():
            launch_kwargs["channel"] = "chrome"
        browser = await playwright.chromium.launch(**launch_kwargs)
        ctx_args: dict = {"viewport": {"width": 1280, "height": 900}}
        if state:
            ctx_args["storage_state"] = state
        context = await browser.new_context(**ctx_args)
        return context

    # ------------------------------------------------------------------
    # Login flow — headed browser, user logs in manually
    # ------------------------------------------------------------------

    async def launch_login(self, user_id: str) -> dict:
        """
        Open a headed browser to the platform login page.
        Wait for the user to log in, then save the session.
        Returns {"success": True/False, "handle": str}.
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return {
                "success": False,
                "error": "Playwright is not installed. Run: pip install playwright && playwright install chromium",
            }

        async with async_playwright() as pw:
            context = await self._new_context(pw, headless=False)
            page = await context.new_page()

            log.info("[%s] Opening login page for user %s", self.platform, user_id)
            await page.goto(self.LOGIN_URL, wait_until="domcontentloaded")

            # Wait for the user to log in (detect the home indicator)
            try:
                await page.wait_for_selector(
                    self.HOME_INDICATOR,
                    timeout=LOGIN_TIMEOUT_S * 1000,
                )
            except Exception:
                await context.close()
                return {"success": False, "error": "Login timed out or was cancelled."}

            # Give a moment for any post-login redirects to settle
            await asyncio.sleep(2)

            # Grab the handle
            handle = await self._get_handle(page)

            # Save session state
            state = await context.storage_state()
            session_store.save_session(user_id, self.platform, state)

            await context.close()
            log.info("[%s] Session saved for user %s (handle=%s)", self.platform, user_id, handle)
            return {"success": True, "handle": handle or f"{self.platform}-user"}

    # ------------------------------------------------------------------
    # me() — load session, scrape handle
    # ------------------------------------------------------------------

    async def me(self, access_token: str, user_id: str = "") -> str:
        """Return the account handle by loading the saved session."""
        state = session_store.load_session(user_id, self.platform) if user_id else None
        if not state:
            return f"{self.platform}-browser-user"
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return f"{self.platform}-browser-user"

        async with async_playwright() as pw:
            context = await self._new_context(pw, headless=True, state=state)
            page = await context.new_page()
            await page.goto(self.LOGIN_URL, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            handle = await self._get_handle(page)
            await context.close()
            return handle or f"{self.platform}-browser-user"

    # ------------------------------------------------------------------
    # publish() — headless browser, compose and submit post
    # ------------------------------------------------------------------

    async def publish(self, access_token: str, text: str, user_id: str = "") -> str | None:
        """Publish a text post using the browser. access_token holds user_id for browser mode."""
        uid = user_id or access_token  # In browser mode, access_token stores user_id
        state = session_store.load_session(uid, self.platform)
        if not state:
            raise RuntimeError(
                f"No browser session for {self.platform}. "
                "Connect via Social Hub → Browser Connect first."
            )
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError("Playwright is not installed.")

        async with async_playwright() as pw:
            context = await self._new_context(pw, headless=True, state=state)
            page = await context.new_page()
            try:
                await page.goto(self.LOGIN_URL, wait_until="domcontentloaded")
                await self._ensure_authenticated(page)
                result = await self._compose_post(page, text)
                # Re-save session state (cookies may have been refreshed)
                new_state = await context.storage_state()
                session_store.save_session(uid, self.platform, new_state)
                return result
            finally:
                await context.close()

    async def publish_media(
        self, access_token: str, text: str, data: bytes, filename: str, user_id: str = ""
    ) -> str | None:
        """Publish a post with media attachment using the browser."""
        uid = user_id or access_token
        state = session_store.load_session(uid, self.platform)
        if not state:
            raise RuntimeError(
                f"No browser session for {self.platform}. "
                "Connect via Social Hub → Browser Connect first."
            )
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError("Playwright is not installed.")

        # Write media to a temp file for Playwright file chooser
        tmp = Path(tempfile.mkdtemp()) / filename
        tmp.write_bytes(data)

        async with async_playwright() as pw:
            context = await self._new_context(pw, headless=True, state=state)
            page = await context.new_page()
            try:
                await page.goto(self.LOGIN_URL, wait_until="domcontentloaded")
                await self._ensure_authenticated(page)
                result = await self._compose_media_post(page, text, str(tmp))
                new_state = await context.storage_state()
                session_store.save_session(uid, self.platform, new_state)
                return result
            finally:
                tmp.unlink(missing_ok=True)
                tmp.parent.rmdir()
                await context.close()

    async def _ensure_authenticated(self, page: "Page") -> None:
        await page.wait_for_load_state("domcontentloaded", timeout=15000)
        if self.HOME_INDICATOR:
            try:
                await page.locator(self.HOME_INDICATOR).first.wait_for(state="visible", timeout=10000)
            except Exception as exc:
                raise RuntimeError(
                    f"Authentication required for {self.platform}; browser session expired or login is required"
                ) from exc

    async def fetch_metrics(self, access_token: str, external_id: str) -> dict | None:
        """Browser adapters cannot reliably scrape metrics. Return None."""
        return None

    # ------------------------------------------------------------------
    # Subclass hooks — override these per platform
    # ------------------------------------------------------------------

    async def _get_handle(self, page: "Page") -> str:
        """Scrape the current user's handle/name from the page. Override per platform."""
        return f"{self.platform}-user"

    async def _compose_post(self, page: "Page", text: str) -> str | None:
        """Navigate to compose UI, fill text, submit. Override per platform."""
        raise RuntimeError(f"Browser publishing not implemented for {self.platform}")

    async def _compose_media_post(self, page: "Page", text: str, file_path: str) -> str | None:
        """Navigate to compose UI, attach file, fill text, submit. Override per platform."""
        # Default: fall back to text-only publish
        return await self._compose_post(page, text)
