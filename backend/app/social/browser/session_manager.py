"""
Interactive Browser Session Manager.

Manages headed browser login sessions with:
  • Real-time status monitoring
  • CAPTCHA and 2FA challenge detection
  • Login success detection
  • Explicit user approval and session state encryption
  • Graceful cleanup and cancellation
"""

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Optional

from . import session_store
from .base_browser import BrowserAdapter

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page, Playwright

log = logging.getLogger(__name__)

CAPTCHA_SELECTORS = [
    'iframe[src*="captcha"]',
    'iframe[src*="recaptcha"]',
    'iframe[src*="arkose"]',
    'iframe[src*="funcaptcha"]',
    'iframe[src*="hcaptcha"]',
    'iframe[src*="challenge"]',
    'div[id*="captcha"]',
    'div[class*="captcha"]',
    'div[id*="challenge"]',
    'div[class*="challenge"]',
    '#challenge-stage',
    '[data-testid*="challenge"]',
    '.g-recaptcha',
    '.h-captcha',
]

CHALLENGE_KEYWORDS = [
    "verify you are human",
    "verification code",
    "security check",
    "suspicious activity",
    "confirm your identity",
    "two-factor authentication",
    "enter code",
    "checkpoint",
    "puzzle",
    "unusual activity",
]


class InteractiveSession:
    def __init__(self, user_id: str, platform: str, adapter: BrowserAdapter):
        self.user_id = user_id
        self.platform = platform
        self.adapter = adapter
        self.pw: Optional["Playwright"] = None
        self.browser: Optional["Browser"] = None
        self.context: Optional["BrowserContext"] = None
        self.page: Optional["Page"] = None
        self.created_at = time.time()
        self.status = "initializing"
        self.url = ""
        self.is_captcha = False
        self.is_logged_in = False
        self.handle = ""
        self.error: Optional[str] = None
        self._closed = False
        self._monitor_task: Optional[asyncio.Task] = None

    async def start(self):
        from playwright.async_api import async_playwright

        self.pw = await async_playwright().start()
        from pathlib import Path

        launch_kwargs = {
            "headless": False,
            "args": ["--disable-blink-features=AutomationControlled"],
        }
        if Path("/usr/bin/google-chrome").exists():
            launch_kwargs["channel"] = "chrome"

        self.browser = await self.pw.chromium.launch(**launch_kwargs)
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
        )
        self.page = await self.context.new_page()
        self.status = "opening_page"
        log.info("[%s] Opening login page %s for user %s", self.platform, self.adapter.LOGIN_URL, self.user_id)
        await self.page.goto(self.adapter.LOGIN_URL, wait_until="domcontentloaded")
        self.url = self.page.url
        self.status = "waiting_for_user"
        self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def _monitor_loop(self):
        """Continuously check page URL and elements for CAPTCHA or successful login."""
        while not self._closed:
            try:
                if not self.page or self.page.is_closed():
                    self.status = "closed_by_user"
                    break

                self.url = self.page.url

                # 1. Check for logged in state
                try:
                    is_home = False
                    if self.adapter.HOME_INDICATOR:
                        el = await self.page.query_selector(self.adapter.HOME_INDICATOR)
                        if el is not None:
                            is_home = True

                    if is_home:
                        self.is_logged_in = True
                        self.is_captcha = False
                        self.status = "login_detected"
                        if not self.handle:
                            try:
                                self.handle = await self.adapter._get_handle(self.page)
                            except Exception:
                                pass
                        await asyncio.sleep(1)
                        continue
                except Exception:
                    pass

                # 2. Check for CAPTCHA or security challenges
                captcha_found = False
                for sel in CAPTCHA_SELECTORS:
                    try:
                        if await self.page.query_selector(sel) is not None:
                            captcha_found = True
                            break
                    except Exception:
                        pass

                if not captcha_found:
                    try:
                        text_content = (await self.page.content()).lower()
                        for kw in CHALLENGE_KEYWORDS:
                            if kw in text_content:
                                captcha_found = True
                                break
                    except Exception:
                        pass

                self.is_captcha = captcha_found
                if captcha_found:
                    self.status = "captcha_detected"
                elif self.status == "captcha_detected":
                    self.status = "waiting_for_user"

            except Exception as exc:
                log.debug("[%s] monitor error: %s", self.platform, exc)

            await asyncio.sleep(1.2)

    async def approve(self) -> dict:
        """User explicitly authorizes/approves session. Save cookies and close."""
        if not self.context:
            raise RuntimeError("Browser session not active")

        # Save cookies & localStorage state
        state = await self.context.storage_state()

        # Extract handle if not yet captured
        if not self.handle and self.page and not self.page.is_closed():
            try:
                self.handle = await self.adapter._get_handle(self.page)
            except Exception:
                pass

        handle = self.handle or f"{self.platform}-user"

        # Encrypt and persist session
        session_store.save_session(self.user_id, self.platform, state)
        self.status = "approved"

        await self.close()
        return {"success": True, "handle": handle}

    async def get_screenshot_bytes(self) -> bytes | None:
        """Capture JPEG screenshot bytes from the live page."""
        if not self.page or self.page.is_closed():
            return None
        try:
            return await self.page.screenshot(type="jpeg", quality=55)
        except Exception as exc:
            log.debug("[%s] screenshot error: %s", self.platform, exc)
            return None

    async def get_screenshot_b64(self) -> str | None:
        """Capture base64-encoded JPEG screenshot from the live page."""
        import base64
        raw = await self.get_screenshot_bytes()
        if raw is None:
            return None
        return f"data:image/jpeg;base64,{base64.b64encode(raw).decode()}"

    async def close(self):
        self._closed = True
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
        if self.page and not self.page.is_closed():
            try:
                await self.page.close()
            except Exception:
                pass
        if self.context:
            try:
                await self.context.close()
            except Exception:
                pass
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
        if self.pw:
            try:
                await self.pw.stop()
            except Exception:
                pass
        self.status = "closed"


# In-memory registry of live user sessions: key = f"{user_id}:{platform}"
_sessions: dict[str, InteractiveSession] = {}


def _key(user_id: str, platform: str) -> str:
    return f"{user_id}:{platform}"


async def start_interactive_session(user_id: str, platform: str, adapter: BrowserAdapter) -> InteractiveSession:
    key = _key(user_id, platform)
    old = _sessions.get(key)
    if old:
        await old.close()

    session = InteractiveSession(user_id, platform, adapter)
    _sessions[key] = session
    await session.start()
    return session


def get_interactive_session(user_id: str, platform: str) -> Optional[InteractiveSession]:
    return _sessions.get(_key(user_id, platform))


async def cancel_interactive_session(user_id: str, platform: str) -> bool:
    key = _key(user_id, platform)
    session = _sessions.pop(key, None)
    if session:
        await session.close()
        return True
    return False


async def approve_interactive_session(user_id: str, platform: str) -> dict:
    key = _key(user_id, platform)
    session = _sessions.get(key)
    if not session:
        raise RuntimeError("No active browser session found to approve.")
    res = await session.approve()
    _sessions.pop(key, None)
    return res


async def get_session_screenshot_bytes(user_id: str, platform: str) -> bytes | None:
    session = _sessions.get(_key(user_id, platform))
    if session:
        return await session.get_screenshot_bytes()
    return None


async def get_session_screenshot_b64(user_id: str, platform: str) -> str | None:
    session = _sessions.get(_key(user_id, platform))
    if session:
        return await session.get_screenshot_b64()
    return None

