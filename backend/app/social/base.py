from abc import ABC, abstractmethod
from urllib.parse import urlencode

from . import creds


class SocialAdapter(ABC):
    platform: str

    @property
    def client_id(self) -> str:
        return creds.get(self.platform)[0]

    @property
    def client_secret(self) -> str:
        return creds.get(self.platform)[1]

    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    @abstractmethod
    def auth_url(self, state: str, redirect_uri: str) -> str: ...

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        """Returns {access_token, refresh_token|None, expires_at|None}."""

    @abstractmethod
    async def me(self, access_token: str) -> str:
        """Returns the account handle."""

    @abstractmethod
    async def publish(self, access_token: str, text: str) -> str | None:
        """Publishes text content; returns the platform post id. Raises if unsupported/failed."""

    @abstractmethod
    async def fetch_metrics(self, access_token: str, external_id: str) -> dict | None:
        """Returns {impressions, likes, comments, shares} or None if unavailable."""

    async def publish_media(self, access_token: str, text: str, data: bytes, filename: str) -> str | None:
        raise RuntimeError(
            f"{self.platform} official API needs a publicly reachable media URL for uploads; "
            f"text-only publishing is used instead."
        )


def qs(**params) -> str:
    return urlencode({k: v for k, v in params.items() if v})
