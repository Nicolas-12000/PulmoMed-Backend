"""
Tests exhaustivos para AuthService
Incluye tests de registro, login, validación y tokens
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.auth_service import AuthService, get_auth_service
from app.schemas.auth_schemas import UserRegisterRequest
from app.models.db_models import User, UserRole


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_db():
    """Mock de AsyncSession."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def auth_service(mock_db):
    """Instancia de AuthService con DB mockeada."""
    return AuthService(mock_db)


@pytest.fixture
def sample_user():
    """Usuario de prueba."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "test@universidad.edu"
    user.hashed_password = "$2b$12$hashedpassword"
    user.full_name = "Test User"
    user.role = UserRole.STUDENT
    user.is_active = True
    return user


@pytest.fixture
def register_request():
    """Request de registro válido."""
    return UserRegisterRequest(
        email="nuevo@universidad.edu",
        password="password123",
        full_name="Nuevo Usuario",
        role=UserRole.STUDENT
    )


# =============================================================================
# Tests de Registro (Casos Positivos)
# =============================================================================

class TestAuthServiceRegisterPositive:
    """Tests de registro que DEBEN funcionar."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, auth_service, mock_db, register_request):
        """Registro exitoso de nuevo usuario."""
        # Mock: email no existe
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch("app.services.auth_service.get_password_hash") as mock_hash:
            mock_hash.return_value = "hashed_password"

            # Simular refresh que asigna ID
            async def fake_refresh(user):
                user.id = uuid4()
            mock_db.refresh = fake_refresh

            user = await auth_service.create_user(register_request)

        assert user is not None
        mock_db.add.assert_called_once()
        mock_hash.assert_called_once_with(register_request.password)

    @pytest.mark.asyncio
    async def test_create_user_professor_role(self, auth_service, mock_db):
        """Registro de profesor."""
        request = UserRegisterRequest(
            email="profesor@universidad.edu",
            password="password123",
            full_name="Dr. García",
            role=UserRole.PROFESSOR
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch("app.services.auth_service.get_password_hash") as mock_hash:
            mock_hash.return_value = "hashed"
            user = await auth_service.create_user(request)

        assert user.role == UserRole.PROFESSOR

    @pytest.mark.asyncio
    async def test_get_user_by_email_found(self, auth_service, mock_db, sample_user):
        """Buscar usuario por email - encontrado."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = mock_result

        user = await auth_service.get_user_by_email("test@universidad.edu")

        assert user == sample_user
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_id_found(self, auth_service, mock_db, sample_user):
        """Buscar usuario por ID - encontrado."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = mock_result

        user = await auth_service.get_user_by_id(sample_user.id)

        assert user == sample_user


# =============================================================================
# Tests de Registro (Casos Negativos)
# =============================================================================

class TestAuthServiceRegisterNegative:
    """Tests de registro que NO deben funcionar."""

    @pytest.mark.asyncio
    async def test_create_user_email_already_exists(
        self, auth_service, mock_db, sample_user, register_request
    ):
        """Registro falla si email ya existe."""
        # Mock: email ya existe
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError) as exc_info:
            await auth_service.create_user(register_request)

        assert "ya está registrado" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, auth_service, mock_db):
        """Buscar usuario por email - no encontrado."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        user = await auth_service.get_user_by_email("noexiste@test.com")

        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, auth_service, mock_db):
        """Buscar usuario por ID - no encontrado."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        user = await auth_service.get_user_by_id(uuid4())

        assert user is None


# =============================================================================
# Tests de Autenticación (Casos Positivos)
# =============================================================================

class TestAuthServiceLoginPositive:
    """Tests de login que DEBEN funcionar."""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, mock_db, sample_user):
        """Login exitoso con credenciales correctas."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = mock_result

        with patch("app.services.auth_service.verify_password") as mock_verify:
            mock_verify.return_value = True

            user = await auth_service.authenticate_user(
                "test@universidad.edu",
                "password123"
            )

        assert user == sample_user
        mock_verify.assert_called_once()

    def test_create_token_for_user(self, auth_service, sample_user):
        """Crear token JWT para usuario."""
        with patch("app.services.auth_service.create_access_token") as mock_token:
            mock_token.return_value = "jwt_token_here"

            token = auth_service.create_token_for_user(sample_user)

        assert token == "jwt_token_here"
        mock_token.assert_called_once()
        # Verificar que se pasaron los datos correctos
        call_args = mock_token.call_args[0][0]
        assert "sub" in call_args
        assert "email" in call_args
        assert "role" in call_args


# =============================================================================
# Tests de Autenticación (Casos Negativos)
# =============================================================================

class TestAuthServiceLoginNegative:
    """Tests de login que NO deben funcionar."""

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service, mock_db):
        """Login falla si usuario no existe."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        user = await auth_service.authenticate_user(
            "noexiste@test.com",
            "password123"
        )

        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(
        self, auth_service, mock_db, sample_user
    ):
        """Login falla con contraseña incorrecta."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = mock_result

        with patch("app.services.auth_service.verify_password") as mock_verify:
            mock_verify.return_value = False

            user = await auth_service.authenticate_user(
                "test@universidad.edu",
                "wrong_password"
            )

        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, auth_service, mock_db, sample_user):
        """Login falla si usuario está inactivo."""
        sample_user.is_active = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = mock_result

        with patch("app.services.auth_service.verify_password") as mock_verify:
            mock_verify.return_value = True

            user = await auth_service.authenticate_user(
                "test@universidad.edu",
                "password123"
            )

        assert user is None


# =============================================================================
# Tests de Factory
# =============================================================================

class TestAuthServiceFactory:
    """Tests para el factory de AuthService."""

    def test_get_auth_service_returns_instance(self, mock_db):
        """Factory retorna instancia de AuthService."""
        service = get_auth_service(mock_db)

        assert isinstance(service, AuthService)
        assert service.db == mock_db


# =============================================================================
# Tests de Schemas
# =============================================================================

class TestAuthSchemas:
    """Tests para validación de schemas."""

    def test_register_request_valid(self):
        """Request de registro válido."""
        request = UserRegisterRequest(
            email="test@test.com",
            password="12345678",
            full_name="Test User",
            role=UserRole.STUDENT
        )
        assert request.email == "test@test.com"
        assert request.password == "12345678"

    def test_register_request_default_role(self):
        """Role por defecto es estudiante."""
        request = UserRegisterRequest(
            email="test@test.com",
            password="12345678",
            full_name="Test User"
        )
        assert request.role == UserRole.STUDENT

    def test_register_request_password_too_short(self):
        """Password muy corto lanza error."""
        with pytest.raises(ValueError):
            UserRegisterRequest(
                email="test@test.com",
                password="123",  # Muy corto
                full_name="Test User"
            )

    def test_register_request_invalid_email(self):
        """Email inválido lanza error."""
        with pytest.raises(ValueError):
            UserRegisterRequest(
                email="not-an-email",
                password="12345678",
                full_name="Test User"
            )

    def test_register_request_name_too_short(self):
        """Nombre muy corto lanza error."""
        with pytest.raises(ValueError):
            UserRegisterRequest(
                email="test@test.com",
                password="12345678",
                full_name="A"  # Muy corto
            )
