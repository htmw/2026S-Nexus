from dataclasses import dataclass

from fastapi import Header, HTTPException, Request, status


@dataclass
class AuthUser:
    # Minimal auth context extracted from request headers.
    user_id: str
    role: str


def _normalize_role(role: str | None) -> str:
    value = (role or "").strip().lower()
    if value in {"patient", "therapist", "admin"}:
        return value
    return ""


async def get_current_user(
    x_user_id: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
) -> AuthUser:
    # Header-based auth keeps local development simple while still enforcing access control.
    user_id = (x_user_id or "").strip()
    role = _normalize_role(x_user_role)

    if not user_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    return AuthUser(user_id=user_id, role=role)


async def require_patient(user: AuthUser) -> AuthUser:
    # Only patients can create personal journal entries.
    if user.role != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient role required",
        )
    return user


async def require_therapist(user: AuthUser) -> AuthUser:
    # Only therapists can access therapist-prefixed endpoints.
    if user.role != "therapist":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Therapist role required",
        )
    return user


def reject_therapist_mutations(request: Request, role: str) -> None:
    # Hard guard: therapists are read-only for patient data endpoints.
    if role != "therapist":
        return

    method = request.method.upper()
    path = request.url.path
    protected_path = path.startswith("/api/therapist/patients")
    if protected_path and method in {"POST", "PUT", "PATCH", "DELETE"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Therapist role has read-only access to patient data",
        )