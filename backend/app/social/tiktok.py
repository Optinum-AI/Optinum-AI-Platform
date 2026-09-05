import base64
import hashlib
import httpx

from .. import config
from ..security import decode_oauth_state
from .base import SocialAdapter, qs

OPEN = "https://open.tiktokapis.com/v2"


class TikTokAdapter(SocialAdapter):
    platform = "tiktok"

    def auth_url(self, state: str, redirect_uri: str) -> str:
        verifier = decode_oauth_state(state)["flow"]
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        return (
            "https://www.tiktok.com/v2/auth/authorize/?"
            + qs(
                client_key=self.client_id,
                response_type="code",
                scope="user.info.basic,video.publish,video.list",
                redirect_uri=redirect_uri,
                state=state,
                code_challenge=challenge,
                code_challenge_method="S256",
            )
        )

    async def exchange_code(self, code: str, redirect_uri: str, code_verifier: str = "") -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{OPEN}/oauth/token/",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_key": self.client_id,
                    "client_secret": self.client_secret,
                    "code_verifier": code_verifier,
                },
            )
            r.raise_for_status()
            d = r.json()["data"]
        return {
            "access_token": d["access_token"],
            "refresh_token": d.get("refresh_token"),
            "expires_at": None,
        }

    async def me(self, access_token: str) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{OPEN}/user/info/",
                params={"fields": "username,display_name"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            r.raise_for_status()
            return "@" + r.json()["data"]["user"]["username"]

    async def publish(self, access_token: str, text: str) -> str | None:
        raise RuntimeError(
            "TikTok's Content Posting API requires a video file/URL; text-only posts are not allowed."
        )

    async def fetch_metrics(self, access_token: str, external_id: str) -> dict | None:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{OPEN}/video/query/",
                params={"fields": "id,view_count,like_count,comment_count,share_count"},
                json={"filters": {"video_ids": [external_id]}},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if r.status_code != 200:
                return None
            items = r.json().get("data", {}).get("videos", [])
            if not items:
                return None
            v = items[0]
            return {
                "impressions": v.get("view_count", 0),
                "likes": v.get("like_count", 0),
                "comments": v.get("comment_count", 0),
                "shares": v.get("share_count", 0),
            }
