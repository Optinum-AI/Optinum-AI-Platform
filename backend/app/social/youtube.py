import httpx

from .. import config
from .base import SocialAdapter, qs


class YouTubeAdapter(SocialAdapter):
    platform = "youtube"

    def auth_url(self, state: str, redirect_uri: str) -> str:
        return (
            "https://accounts.google.com/o/oauth2/v2/auth?"
            + qs(
                response_type="code",
                client_id=self.client_id,
                redirect_uri=redirect_uri,
                state=state,
                scope="https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly",
                access_type="offline",
            )
        )

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
            r.raise_for_status()
            d = r.json()
        return {
            "access_token": d["access_token"],
            "refresh_token": d.get("refresh_token"),
            "expires_at": None,
        }

    async def me(self, access_token: str) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={"part": "snippet", "mine": "true"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            r.raise_for_status()
            items = r.json().get("items", [])
            return items[0]["snippet"]["title"] if items else "youtube-channel"

    async def publish(self, access_token: str, text: str) -> str | None:
        raise RuntimeError(
            "YouTube publishes video uploads only; attach a video asset to the pipeline to use this channel."
        )

    async def fetch_metrics(self, access_token: str, external_id: str) -> dict | None:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={"part": "statistics", "id": external_id},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if r.status_code != 200:
                return None
            items = r.json().get("items", [])
            if not items:
                return None
            s = items[0]["statistics"]
            return {
                "impressions": int(s.get("viewCount", 0)),
                "likes": int(s.get("likeCount", 0)),
                "comments": int(s.get("commentCount", 0)),
                "shares": 0,
            }
