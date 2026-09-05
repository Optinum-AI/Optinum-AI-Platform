"""
Unified social-media provider layer.

Wraps an API adapter and a browser adapter for the same platform into a single
SocialAdapter that the rest of the system (agents, scheduler, publisher) can
call transparently.

Strategy:
  1. If the API adapter is configured and working → use it.
  2. If the API adapter is not configured or fails → fall back to the browser adapter.
"""

from __future__ import annotations

import logging

from .base import SocialAdapter

log = logging.getLogger(__name__)


class UnifiedAdapter(SocialAdapter):
    """
    Facade that tries the API adapter first, then falls back to the browser adapter.
    """

    def __init__(self, api_adapter: SocialAdapter, browser_adapter: SocialAdapter):
        self.api = api_adapter
        self.browser = browser_adapter
        self.platform = api_adapter.platform

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def configured(self) -> bool:
        return self.api.configured() or self.browser.configured()

    @property
    def client_id(self) -> str:
        return self.api.client_id

    @property
    def client_secret(self) -> str:
        return self.api.client_secret

    # ------------------------------------------------------------------
    # OAuth — only the API adapter supports this
    # ------------------------------------------------------------------

    def auth_url(self, state: str, redirect_uri: str) -> str:
        return self.api.auth_url(state, redirect_uri)

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        return await self.api.exchange_code(code, redirect_uri)

    # ------------------------------------------------------------------
    # me()
    # ------------------------------------------------------------------

    async def me(self, access_token: str) -> str:
        if self.api.configured():
            try:
                return await self.api.me(access_token)
            except Exception as exc:
                log.debug("[%s] API me() failed (%s), trying browser", self.platform, exc)
        return await self.browser.me(access_token)

    # ------------------------------------------------------------------
    # publish()
    # ------------------------------------------------------------------

    async def publish(self, access_token: str, text: str) -> str | None:
        if self.api.configured():
            try:
                return await self.api.publish(access_token, text)
            except Exception as exc:
                log.info(
                    "[%s] API publish failed (%s), falling back to browser",
                    self.platform,
                    exc,
                )
        return await self.browser.publish(access_token, text)

    # ------------------------------------------------------------------
    # publish_media()
    # ------------------------------------------------------------------

    async def publish_media(
        self, access_token: str, text: str, data: bytes, filename: str
    ) -> str | None:
        if self.api.configured():
            try:
                return await self.api.publish_media(access_token, text, data, filename)
            except Exception as exc:
                log.info(
                    "[%s] API publish_media failed (%s), falling back to browser",
                    self.platform,
                    exc,
                )
        return await self.browser.publish_media(access_token, text, data, filename)

    # ------------------------------------------------------------------
    # fetch_metrics()  — only the API adapter can do this reliably
    # ------------------------------------------------------------------

    async def fetch_metrics(self, access_token: str, external_id: str) -> dict | None:
        if self.api.configured():
            try:
                return await self.api.fetch_metrics(access_token, external_id)
            except Exception:
                pass
        return await self.browser.fetch_metrics(access_token, external_id)
