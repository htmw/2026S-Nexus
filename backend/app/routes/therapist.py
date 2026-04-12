from fastapi import APIRouter, Depends, status

from app.auth import AuthUser, get_current_user, require_therapist
from app.schemas.checkin import (
    TherapistPatientListResponse,
    TherapistPatientEntriesResponse,
    TherapistPatientEntryResponse,
    TherapistPatientProfileResponse,
    TherapistPatientTrendPoint,
    TherapistPatientTrendResponse,
)
from app.services.checkin import (
    get_linked_patients_for_therapist,
    get_patient_entries_for_therapist,
    get_patient_profile_for_therapist,
    get_patient_trend_for_therapist,
)

router = APIRouter(prefix="/therapist", tags=["therapist"])


@router.get(
    "/patients",
    response_model=TherapistPatientListResponse,
    status_code=status.HTTP_200_OK,
    summary="List therapist-linked patients",
)
async def therapist_patients(user: AuthUser = Depends(get_current_user)):
    # Dashboard list for therapist navigation.
    await require_therapist(user)
    patients = await get_linked_patients_for_therapist(user.user_id)
    return TherapistPatientListResponse(patients=[TherapistPatientProfileResponse(**item) for item in patients])


@router.get(
    "/patients/{patient_id}/profile",
    response_model=TherapistPatientProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient profile for therapist detail page",
)
async def therapist_patient_profile(
    patient_id: str,
    user: AuthUser = Depends(get_current_user),
):
    # Therapists can only read linked + sharing-enabled patient records.
    await require_therapist(user)
    profile = await get_patient_profile_for_therapist(user.user_id, patient_id)
    return TherapistPatientProfileResponse(**profile)


@router.get(
    "/patients/{patient_id}/journal",
    response_model=TherapistPatientEntriesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient journal entries in chronological order",
)
async def therapist_patient_journal(
    patient_id: str,
    user: AuthUser = Depends(get_current_user),
):
    # Canonical US24 path. Endpoint is read-only and blocked if sharing is disabled or therapist is unlinked.
    await require_therapist(user)
    entries = await get_patient_entries_for_therapist(user.user_id, patient_id)
    return TherapistPatientEntriesResponse(
        entries=[
            TherapistPatientEntryResponse(
                date=item["date"],
                text=item["text"],
                sentiment_label=item["sentiment_label"],
            )
            for item in entries
        ]
    )


@router.get(
    "/patients/{patient_id}/journal-entries",
    response_model=TherapistPatientEntriesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient journal entries in chronological order",
)
async def therapist_patient_journal_entries(
    patient_id: str,
    user: AuthUser = Depends(get_current_user),
):
    # Backward-compatible alias for existing frontend clients.
    return await therapist_patient_journal(patient_id=patient_id, user=user)


@router.get(
    "/patients/{patient_id}/mood",
    response_model=TherapistPatientTrendResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient mood trend chart data",
)
async def therapist_patient_mood(
    patient_id: str,
    user: AuthUser = Depends(get_current_user),
):
    # Canonical US24 path. Returns analyzed points and yields empty list when none are available.
    await require_therapist(user)
    points = await get_patient_trend_for_therapist(user.user_id, patient_id)
    return TherapistPatientTrendResponse(
        points=[
            TherapistPatientTrendPoint(
                date=item["date"],
                sentiment_label=item["sentiment_label"],
                confidence_score=item["confidence_score"],
            )
            for item in points
        ]
    )


@router.get(
    "/patients/{patient_id}/mood-trend",
    response_model=TherapistPatientTrendResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient mood trend chart data",
)
async def therapist_patient_mood_trend(
    patient_id: str,
    user: AuthUser = Depends(get_current_user),
):
    # Backward-compatible alias for existing frontend clients.
    return await therapist_patient_mood(patient_id=patient_id, user=user)
