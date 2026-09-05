import json

import httpx

from .base import SocialAdapter


class DiscordAdapter(SocialAdapter):
    platform = "discord"

    def configured(self) -> bool:
        return bool(self.client_id)

    def auth_url(self, state: str, redirect_uri: str) -> str:
        raise RuntimeError("Discord uses a channel webhook; paste it in Integrations instead of OAuth.")

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        raise RuntimeError("Discord webhook connections do not use OAuth.")

    async def me(self, access_token: str) -> str:
        return "discord-webhook"

    async def publish(self, access_token: str, text: str) -> str | None:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(self.client_id, json={"content": text})
            response.raise_for_status()
            return response.json().get("id") if response.content else None

    async def publish_media(self, access_token: str, text: str, data: bytes, filename: str) -> str | None:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                self.client_id,
                data={"payload_json": json.dumps({"content": text})},
                files={"files[0]": (filename, data)},
            )
            response.raise_for_status()
            return response.json().get("id") if response.content else None

    async def fetch_metrics(self, access_token: str, external_id: str) -> dict | None:
        return None
