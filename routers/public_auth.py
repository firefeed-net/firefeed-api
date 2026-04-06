"""Public authentication endpoints for FireFeed API - maintaining backward compatibility with monolithic version."""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import bcrypt
import hmac

from firefeed_core.api_client.client import APIClient
from firefeed_core.auth.token_manager import ServiceTokenManager
from firefeed_core.exceptions import ServiceException
from firefeed_core.models.base_models import UserResponse, Token, UserCreate, UserUpdate, PasswordResetRequest, PasswordResetConfirm, EmailVerificationRequest, ResendVerificationRequest, SuccessResponse
from config.environment import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["authentication"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication token"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)

# Pydantic models for public API (backward compatible with monolithic version)

class UserCreatePublic(UserCreate):
    """User creation model for public API."""
    pass

class UserUpdatePublic(UserUpdate):
    """User update model for public API."""
    pass

class PasswordResetRequestPublic(PasswordResetRequest):
    """Password reset request model for public API."""
    pass

class PasswordResetConfirmPublic(PasswordResetConfirm):
    """Password reset confirm model for public API."""
    pass

class EmailVerificationRequestPublic(EmailVerificationRequest):
    """Email verification request model for public API."""
    pass

class ResendVerificationRequestPublic(ResendVerificationRequest):
    """Resend verification request model for public API."""
    pass

class HTTPError(BaseModel):
    """Error response model for public API."""
    detail: str

# JWT Token models
class TokenPublic(Token):
    """Token response model for public API."""
    pass

class TokenData(BaseModel):
    """Token data model for public API."""
    user_id: Optional[int] = None

# Service token manager for internal API communication
def get_service_token_manager():
    """Get service token manager for internal API communication."""
    return ServiceTokenManager(
        secret_key=settings.jwt_secret_key,
        issuer="firefeed-api"
    )

def get_api_client():
    """Get API client for internal API communication."""
    return APIClient(
        base_url=settings.internal_api_url,
        token=settings.internal_api_token,
        service_id="firefeed-api-public"
    )

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token for public API."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = ServiceTokenManager(
        secret_key=settings.jwt_secret_key,
        issuer="firefeed-api"
    ).create_token(to_encode)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str):
    """Verify password hash using bcrypt with constant-time comparison."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except (ValueError, TypeError):
        return False

def get_password_hash(password: str):
    """Generate password hash using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

ACCESS_TOKEN_EXPIRE_MINUTES = 30
# Dummy bcrypt hash for timing attack mitigation - uses 12 rounds matching bcrypt.gensalt() default
_DUMMY_PASSWORD_HASH = "$2b$12$LJ3m4ys3Lk0T5kK0Lk0Lk0Lk0Lk0Lk0Lk0Lk0Lk0Lk0Lk0Lk0Lk0"

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
    Register a new user account with email verification.
    
    This endpoint creates a new user account and sends a verification email.
    The user account will remain inactive until email verification is completed.
    
    **Process:**
    1. Validate email format and password strength
    2. Check if email is already registered
    3. Create user account (inactive state)
    4. Generate and send verification code via email
    5. Return user information
    
    **Rate limit:** 5 requests per minute
    """,
    responses={
        201: {
            "description": "User successfully registered",
            "model": UserResponse
        },
        400: {
            "description": "Bad Request - Email already registered or invalid data",
            "model": HTTPError
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def register_user(
    request: Request, 
    user: UserCreatePublic, 
    background_tasks: BackgroundTasks,
    api_client: APIClient = Depends(get_api_client)
):
    """Register a new user (backward compatible with monolithic version)."""
    try:
        # Check if user already exists
        try:
            existing_user_response = await api_client.get(f"/api/v1/internal/users/by-email/{user.email}")
            if existing_user_response.get("exists", False):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        except ServiceException:
            # User doesn't exist, continue with registration
            pass
        
        # Create user
        user_data = {
            "email": user.email,
            "password": user.password,
            "language": user.language
        }
        
        user_response = await api_client.post("/api/v1/internal/users", json_data=user_data)
        
        # Generate verification code using cryptographically secure random
        verification_code = f"{secrets.randbelow(1000000):06d}"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        # Save verification code
        verification_data = {
            "user_id": user_response["id"],
            "verification_code": verification_code,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await api_client.post("/api/v1/internal/user-verification-codes", json_data=verification_data)
        
        # Send verification email (background task)
        background_tasks.add_task(
            send_verification_email, 
            user.email, 
            verification_code, 
            user.language
        )
        
        return UserResponse(**user_response)
        
    except ServiceException as e:
        logger.error(f"Service error in register_user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error in register_user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post(
    "/verify",
    response_model=SuccessResponse,
    summary="Verify user email",
    description="""
    Verify user email address using the verification code sent during registration.
    
    This endpoint activates the user account after successful email verification.
    
    **Process:**
    1. Validate verification code format (6 digits)
    2. Find user by email and active verification code
    3. Activate user account
    4. Mark verification code as used
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "Email successfully verified",
            "model": SuccessResponse
        },
        400: {
            "description": "Bad Request - Invalid verification code or email",
            "model": HTTPError
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def verify_user(
    request: Request, 
    verification_request: EmailVerificationRequestPublic,
    api_client: APIClient = Depends(get_api_client)
):
    """Verify user email (backward compatible with monolithic version)."""
    try:
        # Get user by email
        user_response = await api_client.get(f"/api/v1/internal/users/by-email/{verification_request.email}")
        
        if not user_response.get("exists", False):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code or email")
        
        user = user_response.get("user", {})
        
        if user.get("is_verified", False):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already verified")
        
        # Activate user and use verification code
        activation_data = {
            "user_id": user["id"],
            "verification_code": verification_request.code
        }
        
        result = await api_client.post("/api/v1/internal/users/activate", json_data=activation_data)
        
        if not result.get("success", False):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code or email")
        
        return SuccessResponse(message="User successfully verified")
        
    except ServiceException as e:
        logger.error(f"Service error in verify_user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error in verify_user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post(
    "/resend-verification",
    response_model=SuccessResponse,
    summary="Resend verification code",
    description="""
    Resend verification code to user's email if account is not verified yet.
    
    **Process:**
    1. Validate email exists and user is not verified
    2. Generate new verification code
    3. Send verification email
    
    **Rate limit:** 5 requests per minute
    """,
    responses={
        200: {
            "description": "Verification code resent",
            "model": SuccessResponse
        },
        400: {
            "description": "Bad Request - Email not found or already verified",
            "model": HTTPError
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def resend_verification(
    request: Request, 
    resend_request: ResendVerificationRequestPublic,
    background_tasks: BackgroundTasks,
    api_client: APIClient = Depends(get_api_client)
):
    """Resend verification code (backward compatible with monolithic version)."""
    try:
        # Get user by email
        user_response = await api_client.get(f"/api/v1/internal/users/by-email/{resend_request.email}")
        
        if not user_response.get("exists", False):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not found")
        
        user = user_response.get("user", {})
        
        if user.get("is_verified", False):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already verified")
        
        # Generate new verification code using cryptographically secure random
        verification_code = f"{secrets.randbelow(1000000):06d}"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        # Save verification code
        verification_data = {
            "user_id": user["id"],
            "verification_code": verification_code,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await api_client.post("/api/v1/internal/user-verification-codes", json_data=verification_data)
        
        # Send verification email (background task)
        background_tasks.add_task(
            send_verification_email, 
            resend_request.email, 
            verification_code, 
            user.get("language", "en")
        )
        
        return SuccessResponse(message="Verification code sent")
        
    except ServiceException as e:
        logger.error(f"Service error in resend_verification: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error in resend_verification: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post(
    "/login",
    response_model=TokenPublic,
    summary="Authenticate user",
    description="""
    Authenticate user and return JWT access token.
    
    This endpoint verifies user credentials and returns a JWT token for API access.
    The user account must be active (email verified) to login successfully.
    
    **Process:**
    1. Validate email and password
    2. Check if user exists and password is correct
    3. Verify account is active (email verified)
    4. Generate and return JWT access token
    
    **Token validity:** 30 minutes
    
    **Rate limit:** 10 requests per minute
    """,
    responses={
        200: {
            "description": "Authentication successful",
            "model": TokenPublic
        },
        401: {
            "description": "Unauthorized - Invalid credentials or account not verified",
            "model": HTTPError
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def login_user(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    api_client: APIClient = Depends(get_api_client)
):
    """Authenticate user (backward compatible with monolithic version)."""
    try:
        # Get user by email
        user_response = await api_client.get(f"/api/v1/internal/users/by-email/{form_data.username}")

        user_exists = user_response.get("exists", False)
        user = user_response.get("user", {})

        # Always run bcrypt.checkpw to prevent timing attacks
        # Use a dummy hash for non-existent users to maintain constant time
        stored_hash = user.get("password_hash", "")
        if not user_exists:
            stored_hash = _DUMMY_PASSWORD_HASH

        # Verify password - always run this even if user doesn't exist
        password_valid = verify_password(form_data.password, stored_hash)

        # Only raise error after constant-time comparison completes
        if not user_exists or not password_valid:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

        # Check if account is verified
        if not user.get("is_verified", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account not verified.",
            )

        # Check if account is not deleted
        if user.get("is_deleted", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account deactivated.",
            )

        # Generate access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": str(user["id"])}, expires_delta=access_token_expires)

        return TokenPublic(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except ServiceException as e:
        logger.error(f"Service error in login_user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error in login_user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post(
    "/reset-password/request",
    summary="Request password reset",
    description="""
    Request a password reset token to be sent to the user's email.
    
    This endpoint initiates the password reset process by sending a reset link
    to the user's email address. The link will be valid for 1 hour.
    
    **Process:**
    1. Validate email format
    2. Check if user exists (without revealing existence)
    3. Generate secure reset token
    4. Send password reset email with secure link
    
    **Security note:** Always returns success message regardless of email existence
    to prevent email enumeration attacks.
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "Password reset email sent (if email exists)",
            "content": {
                "application/json": {
                    "example": {"message": "If email exists, reset instructions have been sent"}
                }
            }
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def request_password_reset(
    request: Request, 
    password_reset_request: PasswordResetRequestPublic,
    background_tasks: BackgroundTasks,
    api_client: APIClient = Depends(get_api_client)
):
    """Request password reset (backward compatible with monolithic version)."""
    try:
        # Get user by email
        user_response = await api_client.get(f"/api/v1/internal/users/by-email/{password_reset_request.email}")
        
        if not user_response.get("exists", False):
            # Always return success to prevent email enumeration
            return {"message": "If email exists, reset instructions have been sent"}
        
        user = user_response.get("user", {})
        
        # Generate reset token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Save reset token
        reset_data = {
            "user_id": user["id"],
            "token": token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await api_client.post("/api/v1/internal/password-reset-tokens", json_data=reset_data)
        
        # Send reset email (background task)
        background_tasks.add_task(
            send_password_reset_email, 
            password_reset_request.email, 
            token, 
            user.get("language", "en")
        )
        
        return {"message": "If email exists, reset instructions have been sent"}
        
    except ServiceException as e:
        logger.error(f"Service error in request_password_reset: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error in request_password_reset: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post(
    "/reset-password/confirm",
    summary="Confirm password reset",
    description="""
    Confirm password reset using the token from email and set new password.
    
    This endpoint completes the password reset process by validating the reset token
    and updating the user's password.
    
    **Process:**
    1. Validate token format and new password strength
    2. Verify reset token exists and is not expired
    3. Update user password (hashed)
    4. Delete used reset token
    
    **Security:** Token is single-use and expires after 1 hour.
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "Password successfully reset",
            "content": {
                "application/json": {
                    "example": {"message": "Password successfully reset"}
                }
            }
        },
        400: {
            "description": "Bad Request - Invalid or expired token",
            "model": HTTPError
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def confirm_password_reset(
    request: Request, 
    password_reset_confirm: PasswordResetConfirmPublic,
    api_client: APIClient = Depends(get_api_client)
):
    """Confirm password reset (backward compatible with monolithic version)."""
    try:
        # Verify and update password
        new_password_hash = get_password_hash(password_reset_confirm.new_password)
        
        reset_data = {
            "token": password_reset_confirm.token,
            "new_password_hash": new_password_hash
        }
        
        result = await api_client.post("/api/v1/internal/password-reset-tokens/confirm", json_data=reset_data)
        
        if not result.get("success", False):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
        
        return {"message": "Password successfully reset"}
        
    except ServiceException as e:
        logger.error(f"Service error in confirm_password_reset: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error in confirm_password_reset: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# Helper functions for email sending (simplified for now)
async def send_verification_email(email: str, code: str, language: str):
    """Send verification email."""
    logger.info(f"Sending verification email to {email} with code {code} in {language}")

async def send_password_reset_email(email: str, token: str, language: str):
    """Send password reset email."""
    logger.info(f"Sending password reset email to {email} with token {token} in {language}")