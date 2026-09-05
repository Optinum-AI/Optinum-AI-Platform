from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

from .. import security
from ..social import creds

router = APIRouter(prefix="/settings", tags=["settings"])


class CredsIn(BaseModel):
    client_id: str
    client_secret: str

    @field_validator("client_id")
    @classmethod
    def validate_client_id(cls, value: str) -> str:
        return value.strip()


@router.get("/integrations")
def list_integrations(user=Depends(security.get_current_user)):
    return creds.status_map()


@router.put("/integrations/{platform}")
def put_integration(platform: str, body: CredsIn, user=Depends(security.get_current_user)):
    if platform not in creds.PLATFORM_LABELS:
        raise HTTPException(status_code=404, detail="Unknown integration")
    if platform == "discord" and not body.client_id.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=422,
            detail="Discord requires the complete webhook URL beginning with https://discord.com/api/webhooks/",
        )
    if platform == "discord" and body.client_secret != "webhook":
        raise HTTPException(status_code=422, detail='Discord webhook type must be exactly "webhook".')
    creds.set_creds(platform, body.client_id.strip(), body.client_secret.strip())
    return {"ok": True, "configured": creds.configured(platform)}
