import httpx

from .. import config
from .base import SocialAdapter, qs

API = "https://api.x.com"


class XAdapter(SocialAdapter):
    platform = "x"

    def auth_url(self, state: str, redirect_uri: str) -> str:
        return (
            "https://x.com/i/oauth2/authorize?"
            + qs(
                response_type="code",
                client_id=self.client_id,
                redirect_uri=redirect_uri,
                scope="tweet.read tweet.write users.read offline.access",
                state=state,
            )
        )

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{API}/2/oauth2/token",
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
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
            r = await client.get(f"{API}/2/users/me", headers={"Authorization": f"Bearer {access_token}"})
            r.raise_for_status()
            return "@" + r.json()["data"]["username"]

    async def publish(self, access_token: str, text: str) -> str | None:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{API}/2/tweets",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"text": text[:280]},
            )
            r.raise_for_status()
            return r.json()["data"]["id"]

    async def publish_media(self, access_token: str, text: str, data: bytes, filename: str) -> str | None:
        async with httpx.AsyncClient(timeout=60) as client:
            up = await client.post(
                "https://upload.twitter.com/1.1/media/upload.json",
                headers={"Authorization": f"Bearer {access_token}"},
                files={"media": (filename, data)},
            )
            up.raise_for_status()
            media_id = up.json()["media_id_string"]
            r = await client.post(
                f"{API}/2/tweets",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"text": text[:280], "media": {"media_ids": [media_id]}},
            )
            r.raise_for_status()
            return r.json()["data"]["id"]

    async def fetch_metrics(self, access_token: str, external_id: str) -> dict | None:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{API}/2/tweets/{external_id}",
                params={"tweet.fields": "public_metrics"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if r.status_code != 200:
                return None
            m = r.json()["data"]["public_metrics"]
            return {
                "impressions": m.get("impression_count", 0),
                "likes": m.get("like_count", 0),
                "comments": m.get("reply_count", 0),
                "shares": m.get("repost_count", 0),
            }
