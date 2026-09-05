import httpx

from .. import config
from .base import SocialAdapter, qs

API = "https://api.linkedin.com"


class LinkedInAdapter(SocialAdapter):
    platform = "linkedin"

    def auth_url(self, state: str, redirect_uri: str) -> str:
        return (
            "https://www.linkedin.com/oauth/v2/authorization?"
            + qs(
                response_type="code",
                client_id=self.client_id,
                redirect_uri=redirect_uri,
                scope="openid profile w_member_social",
                state=state,
            )
        )

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://www.linkedin.com/oauth/v2/accessToken",
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
                f"{API}/v2/userinfo", headers={"Authorization": f"Bearer {access_token}"}
            )
            r.raise_for_status()
            d = r.json()
            return d.get("name", "linkedin-user")

    async def publish(self, access_token: str, text: str) -> str | None:
        async with httpx.AsyncClient(timeout=30) as client:
            urn = await self._person_urn(client, access_token)
            r = await client.post(
                f"{API}/rest/posts",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "LinkedIn-Version": "202401",
                    "Content-Type": "application/json",
                },
                json={
                    "author": urn,
                    "commentary": text,
                    "visibility": "PUBLIC",
                    "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": []},
                    "lifecycleState": "PUBLISHED",
                    "isReshareDisabledByAuthor": False,
                },
            )
            r.raise_for_status()
            return r.headers.get("X-RestLi-Id", r.text or None)

    async def _person_urn(self, client: httpx.AsyncClient, access_token: str) -> str:
        r = await client.get(f"{API}/v2/userinfo", headers={"Authorization": f"Bearer {access_token}"})
        r.raise_for_status()
        return r.json()["sub"]

    async def fetch_metrics(self, access_token: str, external_id: str) -> dict | None:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{API}/rest/posts/{external_id}",
                params={"fields": "stats"},
                headers={"Authorization": f"Bearer {access_token}", "LinkedIn-Version": "202401"},
            )
            if r.status_code != 200:
                return None
            s = r.json().get("stats", {})
            return {
                "impressions": s.get("impressionCount", 0),
                "likes": s.get("likeCount", 0),
                "comments": s.get("commentCount", 0),
                "shares": s.get("shareCount", 0),
            }
