import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse
from app.services.auth import verify_password, create_access_token
from app.services.user import create_user, get_user_by_email

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(user: UserRegister):
    try:
        user_doc = await create_user(
            name=user.name,
            email=user.email,
            password=user.password,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    token = create_access_token(user_doc["_id"])

    logger.info("New user registered: %s", user_doc["email"])

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_doc["_id"],
            name=user_doc["name"],
            email=user_doc["email"],
        ),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
)
async def login(credentials: UserLogin):
    user_doc = await get_user_by_email(credentials.email)

    if not user_doc or not verify_password(credentials.password, user_doc["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user_doc["_id"])

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_doc["_id"],
            name=user_doc["name"],
            email=user_doc["email"],
        ),
    )
