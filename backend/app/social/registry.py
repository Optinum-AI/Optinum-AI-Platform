from .base import SocialAdapter
from .linkedin import LinkedInAdapter
from .meta import FacebookAdapter, InstagramAdapter
from .tiktok import TikTokAdapter
from .x import XAdapter
from .youtube import YouTubeAdapter
from .discord import DiscordAdapter

ADAPTERS: dict[str, SocialAdapter] = {
    a.platform: a
    for a in (XAdapter(), LinkedInAdapter(), FacebookAdapter(), InstagramAdapter(), YouTubeAdapter(), TikTokAdapter(), DiscordAdapter())
}


def get_adapter(platform: str) -> SocialAdapter | None:
    try:
        from .unified_registry import get_unified_adapter
        unified = get_unified_adapter(platform)
        if unified is not None:
            return unified
    except Exception:
        pass
    return ADAPTERS.get(platform)

