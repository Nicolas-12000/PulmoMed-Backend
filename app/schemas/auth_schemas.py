"""
Pydantic Schemas for Authentication
DTOs para requests/responses de autenticación
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.db_models import UserRole


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class UserRegisterRequest(BaseModel):
    """Request para registro de usuario"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Mínimo 8 caracteres")
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = UserRole.STUDENT

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "estudiante@universidad.edu",
                "password": "password123",
                "full_name": "María García López",
                "role": "student"
            }
        }
    }


class UserLoginRequest(BaseModel):
    """Request para login"""
    email: EmailStr
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "estudiante@universidad.edu",
                "password": "password123"
            }
        }
    }


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class UserResponse(BaseModel):
    """Response con datos de usuario (sin password)"""
    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Response con token JWT"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    """Response genérico con mensaje"""
    message: str
    success: bool = True
