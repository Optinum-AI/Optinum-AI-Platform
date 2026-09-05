"""
Unified registry for social-media adapters.

Combines the existing API adapters with the Playwright browser adapters
into UnifiedAdapter instances. This provides automatic fallback to browser
automation when API credentials are missing or when API calls fail.
"""

from .base import SocialAdapter
from .registry import ADAPTERS as API_ADAPTERS
from .provider import UnifiedAdapter
from .browser.x_browser import XBrowserAdapter
from .browser.linkedin_browser import LinkedInBrowserAdapter
from .browser.facebook_browser import FacebookBrowserAdapter
from .browser.instagram_browser import InstagramBrowserAdapter
from .browser.youtube_browser import YouTubeBrowserAdapter
from .browser.tiktok_browser import TikTokBrowserAdapter
from .browser.discord_browser import DiscordBrowserAdapter

BROWSER_ADAPTERS: dict[str, SocialAdapter] = {
    "x": XBrowserAdapter(),
    "linkedin": LinkedInBrowserAdapter(),
    "facebook": FacebookBrowserAdapter(),
    "instagram": InstagramBrowserAdapter(),
    "youtube": YouTubeBrowserAdapter(),
    "tiktok": TikTokBrowserAdapter(),
    "discord": DiscordBrowserAdapter(),
}

UNIFIED_ADAPTERS: dict[str, SocialAdapter] = {
    platform: UnifiedAdapter(api_adapter, BROWSER_ADAPTERS[platform])
    for platform, api_adapter in API_ADAPTERS.items()
    if platform in BROWSER_ADAPTERS
}


def get_unified_adapter(platform: str) -> SocialAdapter | None:
    """Get the unified (API + browser fallback) adapter for a platform."""
    return UNIFIED_ADAPTERS.get(platform)
