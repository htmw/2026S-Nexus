"""
Sharing service: patient-controlled therapist access management.

Data model (matches the existing migration schema):
  therapist_patient_links  { therapist_id, patient_id, active: bool, linked_at }
  patient_profiles         { patient_id, name, email, sharing_enabled: bool }

sharing_enabled on patient_profiles is a global toggle: when False, no
therapist can view this patient's data regardless of the link being active.
Per-therapist granularity is handled by the `active` flag on the link doc.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.database import get_database

logger = logging.getLogger(__name__)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _db_required() -> None:
    if get_database() is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sharing settings require database connectivity",
        )


# ── Patient profile helpers ──────────────────────────────────────────────────

async def _get_or_create_profile(patient_id: str) -> dict:
    """
    Return the patient_profiles document, creating a minimal one if absent.
    The profile is seeded from the users collection when first created.
    """
    db = get_database()
    profile = await db.patient_profiles.find_one({"patient_id": patient_id})
    if profile:
        return profile

    # Seed from users collection so name/email are pre-filled
    user = await db.users.find_one({"_id": patient_id})
    new_profile = {
        "patient_id": patient_id,
        "name": user["name"] if user else "Unknown",
        "email": user["email"] if user else "",
        "sharing_enabled": False,   # off by default; patient opts in
        "created_at": _now_utc(),
    }
    await db.patient_profiles.insert_one(new_profile)
    return new_profile


# ── Sharing preference ───────────────────────────────────────────────────────

async def get_sharing_enabled(patient_id: str) -> bool:
    """Return the patient's global sharing flag."""
    _db_required()
    db = get_database()
    profile = await db.patient_profiles.find_one({"patient_id": patient_id})
    return bool((profile or {}).get("sharing_enabled", False))


async def set_sharing_enabled(patient_id: str, enabled: bool) -> dict:
    """
    Upsert the patient_profiles document and set sharing_enabled.
    Returns the updated profile dict.
    """
    _db_required()
    db = get_database()
    await _get_or_create_profile(patient_id)
    await db.patient_profiles.update_one(
        {"patient_id": patient_id},
        {"$set": {"sharing_enabled": enabled, "updated_at": _now_utc()}},
    )
    logger.info("Patient %s set sharing_enabled=%s", patient_id, enabled)
    return {"patient_id": patient_id, "sharing_enabled": enabled}


# ── Therapist linking ────────────────────────────────────────────────────────

async def get_patient_therapist_links(patient_id: str) -> list[dict]:
    """
    Return all active therapist links for a patient, including the current
    global sharing_enabled flag.
    """
    _db_required()
    db = get_database()
    cursor = db.therapist_patient_links.find({"patient_id": patient_id})
    links = await cursor.to_list(length=50)
    profile = await db.patient_profiles.find_one({"patient_id": patient_id}) or {}
    sharing_enabled = bool(profile.get("sharing_enabled", False))

    return [
        {
            "therapist_id": link["therapist_id"],
            "active": bool(link.get("active", True)),
            "linked_at": link.get("linked_at"),
            "sharing_enabled": sharing_enabled,
        }
        for link in links
    ]


async def link_patient_to_therapist(patient_id: str, therapist_id: str) -> dict:
    """
    Create or re-activate a therapist ↔ patient link.
    Also ensures a patient_profiles document exists.
    """
    _db_required()
    db = get_database()

    # Ensure profile exists
    await _get_or_create_profile(patient_id)

    existing = await db.therapist_patient_links.find_one(
        {"therapist_id": therapist_id, "patient_id": patient_id}
    )
    if existing:
        if not existing.get("active", True):
            # Re-activate a previously removed link
            await db.therapist_patient_links.update_one(
                {"therapist_id": therapist_id, "patient_id": patient_id},
                {"$set": {"active": True, "relinked_at": _now_utc()}},
            )
            logger.info("Re-linked therapist %s ↔ patient %s", therapist_id, patient_id)
        return {"linked": True, "therapist_id": therapist_id}

    await db.therapist_patient_links.insert_one(
        {
            "therapist_id": therapist_id,
            "patient_id": patient_id,
            "active": True,
            "linked_at": _now_utc(),
        }
    )
    logger.info("Linked therapist %s ↔ patient %s", therapist_id, patient_id)
    return {"linked": True, "therapist_id": therapist_id}


async def unlink_patient_from_therapist(patient_id: str, therapist_id: str) -> dict:
    """
    Deactivate a therapist link (soft-delete: sets active=False).
    Hard-deletes are not used so the audit trail is preserved.
    """
    _db_required()
    db = get_database()
    result = await db.therapist_patient_links.update_one(
        {"therapist_id": therapist_id, "patient_id": patient_id},
        {"$set": {"active": False, "unlinked_at": _now_utc()}},
    )
    unlinked = result.modified_count > 0
    logger.info(
        "Unlinked therapist %s ↔ patient %s (found=%s)",
        therapist_id,
        patient_id,
        unlinked,
    )
    return {"unlinked": unlinked, "therapist_id": therapist_id}
