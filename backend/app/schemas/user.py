from pydantic import BaseModel, EmailStr, Field


# ── Public registration (patients only) ─────────────────────────────────────

class UserRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)

    model_config = {
        "json_schema_extra": {
            "examples": [{"name": "Jane Doe", "email": "jane@example.com", "password": "securePass1"}]
        }
    }


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Admin-only therapist provisioning ───────────────────────────────────────

class TherapistProvisionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)

    model_config = {
        "json_schema_extra": {
            "examples": [{"name": "Dr. Smith", "email": "drsmith@clinic.com", "password": "clinicPass1"}]
        }
    }


class TherapistProvisionResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str = "therapist"
    message: str = "Therapist account created. Share the ID with their patients."