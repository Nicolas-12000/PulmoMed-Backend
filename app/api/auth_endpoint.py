"""
Authentication Endpoints - /auth/*
Endpoints para registro y login de usuarios
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.db_models import User
from app.schemas.auth_schemas import (
    MessageResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# OAuth2 scheme para extraer token del header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# =============================================================================
# DEPENDENCIES
# =============================================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency que extrae y valida el usuario actual del token JWT

    Raises:
        HTTPException 401: Si el token es inválido o usuario no existe
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = decode_access_token(token)
    if token_data is None or token_data.user_id is None:
        raise credentials_exception

    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(token_data.user_id)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )

    return user


async def get_current_active_professor(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency que requiere rol de profesor o admin"""
    if current_user.role.value not in ["professor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de profesor"
        )
    return current_user


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario"
)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Registra un nuevo usuario en el sistema.

    - **email**: Email único del usuario
    - **password**: Contraseña (mínimo 8 caracteres)
    - **full_name**: Nombre completo
    - **role**: student | professor | admin
    """
    auth_service = AuthService(db)

    try:
        user = await auth_service.create_user(request)
        logger.info(f"Usuario registrado: {user.email}")
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión"
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Autentica usuario y retorna token JWT.

    Usar con OAuth2PasswordRequestForm (form-data):
    - **username**: Email del usuario
    - **password**: Contraseña

    El token retornado debe usarse en header:
    `Authorization: Bearer <token>`
    """
    auth_service = AuthService(db)

    user = await auth_service.authenticate_user(
        email=form_data.username,
        password=form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_token_for_user(user)
    logger.info(f"Usuario autenticado: {user.email}")

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post(
    "/login/json",
    response_model=TokenResponse,
    summary="Iniciar sesión (JSON)"
)
async def login_json(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Autentica usuario con JSON body (alternativa a form-data).
    Útil para clientes como Unity que prefieren JSON.
    """
    auth_service = AuthService(db)

    user = await auth_service.authenticate_user(
        email=request.email,
        password=request.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )

    access_token = auth_service.create_token_for_user(user)
    logger.info(f"Usuario autenticado: {user.email}")

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtener usuario actual"
)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Retorna información del usuario autenticado.
    Requiere token JWT válido en header Authorization.
    """
    return current_user


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Cerrar sesión"
)
async def logout(current_user: User = Depends(get_current_user)):
    """
    Cierra la sesión del usuario.

    Nota: Como usamos JWT stateless, el logout es principalmente
    del lado del cliente (eliminar el token almacenado).
    En producción se podría implementar una blacklist de tokens.
    """
    logger.info(f"Usuario cerró sesión: {current_user.email}")
    return MessageResponse(
        message="Sesión cerrada exitosamente",
        success=True
    )
