"""
app/routes/sharing.py

Patient-facing API for managing therapist access to their journal and mood data.

Endpoints
---------
GET    /api/sharing/status          — get global sharing flag + all therapist links
PATCH  /api/sharing/enabled         — toggle global sharing on/off
POST   /api/sharing/link            — link a therapist by ID
DELETE /api/sharing/link/{id}       — deactivate a therapist link
"""

import logging

from fastapi import APIRouter, Depends, status

from app.auth import AuthUser, get_current_user, require_patient
from app.schemas.checkin import (
    SharingStatusResponse,
    SharingToggleRequest,
    TherapistLinkRequest,
    TherapistLinkInfo,
    TherapistLinksResponse,
)
from app.services.sharing import (
    get_patient_therapist_links,
    get_sharing_enabled,
    link_patient_to_therapist,
    set_sharing_enabled,
    unlink_patient_from_therapist,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sharing", tags=["sharing"])


@router.get(
    "/status",
    response_model=TherapistLinksResponse,
    summary="Get therapist links and global sharing status for the authenticated patient",
)
async def get_sharing_status(user: AuthUser = Depends(get_current_user)):
    await require_patient(user)
    links_raw = await get_patient_therapist_links(user.user_id)
    sharing_enabled = await get_sharing_enabled(user.user_id)
    return TherapistLinksResponse(
        links=[TherapistLinkInfo(**l) for l in links_raw],
        sharing_enabled=sharing_enabled,
    )


@router.patch(
    "/enabled",
    response_model=SharingStatusResponse,
    summary="Enable or disable data sharing with all linked therapists",
)
async def toggle_sharing(
    body: SharingToggleRequest,
    user: AuthUser = Depends(get_current_user),
):
    await require_patient(user)
    result = await set_sharing_enabled(user.user_id, body.sharing_enabled)
    return SharingStatusResponse(**result)


@router.post(
    "/link",
    status_code=status.HTTP_201_CREATED,
    summary="Link a therapist to the authenticated patient's account",
)
async def add_therapist_link(
    body: TherapistLinkRequest,
    user: AuthUser = Depends(get_current_user),
):
    await require_patient(user)
    result = await link_patient_to_therapist(user.user_id, body.therapist_id)
    return result


@router.delete(
    "/link/{therapist_id}",
    summary="Deactivate (soft-delete) a therapist link",
)
async def remove_therapist_link(
    therapist_id: str,
    user: AuthUser = Depends(get_current_user),
):
    await require_patient(user)
    result = await unlink_patient_from_therapist(user.user_id, therapist_id)
    return result
