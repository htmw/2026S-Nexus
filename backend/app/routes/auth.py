import logging
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.auth import AuthUser, get_current_user
from app.config import settings
from app.schemas.user import (
    UserRegister, UserLogin, UserResponse, TokenResponse,
    TherapistProvisionRequest, TherapistProvisionResponse,
)
from app.services.auth import verify_password, create_access_token
from app.services.user import create_user, get_user_by_email, get_user_by_id

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])


def _require_admin_key(x_admin_key: str | None = Header(default=None)) -> None:
    """Dependency: validates the X-Admin-Key header. Constant-time comparison."""
    configured = settings.ADMIN_API_KEY
    if not configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Therapist provisioning is not enabled on this server. Set ADMIN_API_KEY in .env",
        )
    if not x_admin_key or not secrets.compare_digest(x_admin_key, configured):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin key",
        )


# ── Public endpoints ─────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient account",
)
async def register(user: UserRegister):
    """Anyone can register as a patient. Therapist accounts are created by admins only."""
    try:
        user_doc = await create_user(
            name=user.name,
            email=user.email,
            password=user.password,
            role="patient",  # hardcoded — clients cannot choose their role
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    token = create_access_token(user_doc["_id"])
    logger.info("New patient registered: %s", user_doc["email"])

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_doc["_id"],
            name=user_doc["name"],
            email=user_doc["email"],
            role=user_doc["role"],
        ),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login — works for both patients and therapists",
)
async def login(credentials: UserLogin):
    """
    Returns a JWT token plus the user's id and role.
    The frontend stores the role and sends it as X-User-Role on subsequent requests.
    """
    user_doc = await get_user_by_email(credentials.email)

    if not user_doc or not verify_password(credentials.password, user_doc["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user_doc["_id"])
    logger.info("%s logged in: %s", user_doc.get("role", "patient"), user_doc["email"])

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_doc["_id"],
            name=user_doc["name"],
            email=user_doc["email"],
            role=user_doc.get("role", "patient"),
        ),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user's profile including their ID and role",
)
async def get_me(user: AuthUser = Depends(get_current_user)):
    """
    Therapists call this to retrieve their own ID, which they then share
    with patients for linking. Patients call it to confirm their account details.
    """
    user_doc = await get_user_by_id(user.user_id)
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(
        id=user_doc["_id"],
        name=user_doc["name"],
        email=user_doc["email"],
        role=user_doc.get("role", user.role),
    )


# ── Admin-only endpoint ──────────────────────────────────────────────────────

@router.post(
    "/admin/therapists",
    response_model=TherapistProvisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Create a therapist account",
    description=(
        "Creates a therapist account with a server-assigned role. "
        "Requires the `X-Admin-Key` header matching `ADMIN_API_KEY` in `.env`. "
        "The returned `id` is what patients enter to link their account."
    ),
)
async def provision_therapist(
    body: TherapistProvisionRequest,
    _: None = Depends(_require_admin_key),
):
    try:
        user_doc = await create_user(
            name=body.name,
            email=body.email,
            password=body.password,
            role="therapist",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    logger.info("Therapist account provisioned: %s (id=%s)", user_doc["email"], user_doc["_id"])

    return TherapistProvisionResponse(
        id=user_doc["_id"],
        name=user_doc["name"],
        email=user_doc["email"],
    )