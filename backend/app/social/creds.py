import json
import os

from .. import config

PATH = config.DATA_DIR / "integrations.json"
_store: dict[str, list[str]] = {}


def _load() -> None:
    global _store
    if PATH.exists():
        try:
            _store = json.loads(PATH.read_text())
        except Exception:
            _store = {}


_load()


def get(platform: str) -> tuple[str, str]:
    override = _store.get(platform)
    if override and override[0] and override[1]:
        return override[0], override[1]
    return config.SOCIAL_CREDS.get(platform, ("", ""))


def set_creds(platform: str, client_id: str, client_secret: str) -> None:
    _store[platform] = [client_id, client_secret]
    PATH.write_text(json.dumps(_store, indent=2))
    os.chmod(PATH, 0o600)


def configured(platform: str) -> bool:
    cid, csec = get(platform)
    return bool(cid and csec)


PLATFORM_LABELS = {
    "google": "Google (Sign-In + YouTube)",
    "x": "X (Twitter)",
    "linkedin": "LinkedIn",
    "facebook": "Facebook (Meta app)",
    "instagram": "Instagram (same Meta app)",
    "youtube": "YouTube (Google Cloud app)",
    "tiktok": "TikTok",
    "discord": "Discord (channel webhook)",
}


def status_map() -> list[dict]:
    out = []
    for platform, label in PLATFORM_LABELS.items():
        cid, _ = get(platform)
        out.append({"platform": platform, "label": label, "configured": configured(platform), "client_id": cid})
    return out
