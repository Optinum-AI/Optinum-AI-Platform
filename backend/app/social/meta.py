import httpx

from .. import config
from .base import SocialAdapter, qs

GRAPH = "https://graph.facebook.com/v19.0"
OAUTH = "https://www.facebook.com/v19.0"


class FacebookAdapter(SocialAdapter):
    platform = "facebook"

    def auth_url(self, state: str, redirect_uri: str) -> str:
        return (
            f"{OAUTH}/dialog/oauth?"
            + qs(
                client_id=self.client_id,
                redirect_uri=redirect_uri,
                state=state,
                scope="pages_show_list,pages_manage_posts,pages_read_engagement",
            )
        )

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{GRAPH}/oauth/access_token",
                params={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
            )
            r.raise_for_status()
            d = r.json()
        return {"access_token": d["access_token"], "refresh_token": None, "expires_at": None}

    async def me(self, access_token: str) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{GRAPH}/me", params={"access_token": access_token})
            r.raise_for_status()
            return r.json().get("name", "facebook-user")

    async def _page(self, client: httpx.AsyncClient, access_token: str) -> tuple[str, str]:
        r = await client.get(f"{GRAPH}/me/accounts", params={"access_token": access_token})
        r.raise_for_status()
        pages = r.json().get("data", [])
        if not pages:
            raise RuntimeError("No Facebook Page available — the official API posts as a Page")
        return pages[0]["id"], pages[0]["access_token"]

    async def publish(self, access_token: str, text: str) -> str | None:
        async with httpx.AsyncClient(timeout=30) as client:
            page_id, page_token = await self._page(client, access_token)
            r = await client.post(
                f"{GRAPH}/{page_id}/feed",
                params={"access_token": page_token},
                json={"message": text},
            )
            r.raise_for_status()
            return r.json()["id"]

    async def publish_media(self, access_token: str, text: str, data: bytes, filename: str) -> str | None:
        async with httpx.AsyncClient(timeout=60) as client:
            page_id, page_token = await self._page(client, access_token)
            r = await client.post(
                f"{GRAPH}/{page_id}/photos",
                params={"access_token": page_token},
                files={"source": (filename, data)},
                data={"caption": text},
            )
            r.raise_for_status()
            return r.json()["id"]

    async def fetch_metrics(self, access_token: str, external_id: str) -> dict | None:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{GRAPH}/{external_id}/insights",
                params={
                    "metric": "post_impressions_unique,post_engagements",
                    "access_token": access_token,
                },
            )
            if r.status_code != 200:
                return None
            data = r.json().get("data", [])
            imp = eng = 0
            for row in data:
                values = row.get("values", [])
                v = values[-1]["value"] if values else 0
                if row.get("name") == "post_impressions_unique":
                    imp = v
                else:
                    eng = v
            return {"impressions": imp, "likes": eng, "comments": 0, "shares": 0}


class InstagramAdapter(FacebookAdapter):
    platform = "instagram"

    def auth_url(self, state: str, redirect_uri: str) -> str:
        return (
            f"{OAUTH}/dialog/oauth?"
            + qs(
                client_id=self.client_id,
                redirect_uri=redirect_uri,
                state=state,
                scope="instagram_basic,instagram_content_publish,pages_show_list",
            )
        )

    async def publish(self, access_token: str, text: str) -> str | None:
        # Instagram's official Content Publishing API requires a media URL
        # (image_url or video_url); caption-only posts are not permitted.
        raise RuntimeError(
            "Instagram's official API requires an image/video asset URL; text-only posts are not allowed."
        )

    async def fetch_metrics(self, access_token: str, external_id: str) -> dict | None:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{GRAPH}/{external_id}/insights",
                params={"metric": "impressions,likes,comments,shares", "access_token": access_token},
            )
            if r.status_code != 200:
                return None
            out = {"impressions": 0, "likes": 0, "comments": 0, "shares": 0}
            for row in r.json().get("data", []):
                values = row.get("values", [])
                v = values[-1]["value"] if values else 0
                key = row.get("name", "").lower()
                if key in out:
                    out[key] = v
            return out
