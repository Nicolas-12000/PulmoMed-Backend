"""
Authentication Service - Business Logic
Servicio para registro, login, y validación de usuarios
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models.db_models import User
from app.schemas.auth_schemas import UserRegisterRequest


class AuthService:
    """Servicio de autenticación (SOLID: Single Responsibility)"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Busca usuario por email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Busca usuario por ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user(self, request: UserRegisterRequest) -> User:
        """
        Crea un nuevo usuario

        Args:
            request: Datos de registro

        Returns:
            Usuario creado

        Raises:
            ValueError: Si el email ya existe
        """
        # Verificar que el email no exista
        existing = await self.get_user_by_email(request.email)
        if existing:
            raise ValueError(f"El email {request.email} ya está registrado")

        # Crear usuario con password hasheado
        user = User(
            email=request.email,
            hashed_password=get_password_hash(request.password),
            full_name=request.full_name,
            role=request.role,
        )

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        Autentica usuario por email y password

        Returns:
            User si credenciales correctas, None si no
        """
        user = await self.get_user_by_email(email)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        return user

    def create_token_for_user(self, user: User) -> str:
        """Crea token JWT para usuario"""
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
        }
        return create_access_token(token_data)


def get_auth_service(db: AsyncSession) -> AuthService:
    """Factory para AuthService (Dependency Injection)"""
    return AuthService(db)
