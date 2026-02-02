"""
Tests unitarios para API endpoints.
Mockea autenticación y base de datos.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException


# =============================================================================
# Tests para exam_endpoint helpers
# =============================================================================


class TestExamEndpointHelpers:
    """Tests para funciones helper de exam endpoint."""

    def test_get_exam_or_404_raises_when_not_found(self):
        """get_exam_or_404 lanza HTTPException cuando examen no existe."""
        from app.api.exam_endpoint import get_exam_or_404

        service_mock = MagicMock()
        service_mock.get_exam = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                get_exam_or_404(uuid4(), service_mock)
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_exam_or_404_returns_exam_when_found(self):
        """get_exam_or_404 retorna examen cuando existe."""
        from app.api.exam_endpoint import get_exam_or_404

        exam_mock = MagicMock()
        exam_mock.id = uuid4()
        exam_mock.title = "Examen de prueba"

        service_mock = MagicMock()
        service_mock.get_exam = AsyncMock(return_value=exam_mock)

        result = await get_exam_or_404(exam_mock.id, service_mock)

        assert result == exam_mock

    def test_verify_exam_ownership_raises_for_non_owner(self):
        """verify_exam_ownership lanza 403 para no-propietario."""
        from app.api.exam_endpoint import verify_exam_ownership

        exam_mock = MagicMock()
        exam_mock.creator_id = uuid4()

        user_mock = MagicMock()
        user_mock.id = uuid4()  # Diferente ID
        user_mock.role.value = "professor"

        with pytest.raises(HTTPException) as exc_info:
            verify_exam_ownership(exam_mock, user_mock)

        assert exc_info.value.status_code == 403

    def test_verify_exam_ownership_allows_owner(self):
        """verify_exam_ownership permite al propietario."""
        from app.api.exam_endpoint import verify_exam_ownership

        user_id = uuid4()

        exam_mock = MagicMock()
        exam_mock.creator_id = user_id

        user_mock = MagicMock()
        user_mock.id = user_id  # Mismo ID
        user_mock.role.value = "professor"

        # No debe lanzar excepción
        verify_exam_ownership(exam_mock, user_mock)

    def test_verify_exam_ownership_allows_admin(self):
        """verify_exam_ownership permite al admin."""
        from app.api.exam_endpoint import verify_exam_ownership

        exam_mock = MagicMock()
        exam_mock.creator_id = uuid4()

        user_mock = MagicMock()
        user_mock.id = uuid4()  # Diferente ID
        user_mock.role.value = "admin"  # Pero es admin

        # No debe lanzar excepción
        verify_exam_ownership(exam_mock, user_mock)


# =============================================================================
# Tests para generate_enrollment_code (en db_models)
# =============================================================================


class TestEnrollmentCode:
    """Tests para generación de código de inscripción."""

    def test_generate_enrollment_code_is_unique(self):
        """generate_enrollment_code genera códigos únicos."""
        from app.models.db_models import generate_enrollment_code

        codes = set()
        for _ in range(100):
            code = generate_enrollment_code()
            assert code not in codes
            codes.add(code)
            assert len(code) == 6

    def test_generate_enrollment_code_format(self):
        """generate_enrollment_code genera código alfanumérico mayúsculas."""
        from app.models.db_models import generate_enrollment_code

        code = generate_enrollment_code()

        assert len(code) == 6
        assert code.isupper()
        # Verificar que no contiene caracteres confusos
        assert '0' not in code
        assert 'O' not in code
        assert 'I' not in code
        assert '1' not in code
        assert 'L' not in code


# =============================================================================
# Tests para rate_limiter
# =============================================================================


class TestRateLimiter:
    """Tests para rate limiter."""

    @pytest.mark.asyncio
    async def test_rate_limit_allows_initial_request(self):
        """Rate limiter permite solicitud inicial."""
        from app.api.rate_limiter import rate_limit, _buckets

        # Limpiar bucket antes del test
        test_key = f"test_client_{uuid4()}"

        # Primera solicitud debe ser permitida
        await rate_limit(test_key, limit=5, window_seconds=60)

        # No debe lanzar excepción
        assert len(_buckets[test_key]) == 1

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_after_limit(self):
        """Rate limiter bloquea después del límite."""
        from app.api.rate_limiter import rate_limit

        test_key = f"test_client_{uuid4()}"

        # Hacer solicitudes hasta el límite
        for _ in range(2):
            await rate_limit(test_key, limit=2, window_seconds=60)

        # La siguiente debe fallar
        with pytest.raises(HTTPException) as exc_info:
            await rate_limit(test_key, limit=2, window_seconds=60)

        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_rate_limit_different_keys_isolated(self):
        """Rate limiter aísla diferentes clientes."""
        from app.api.rate_limiter import rate_limit

        key1 = f"client_1_{uuid4()}"
        key2 = f"client_2_{uuid4()}"

        # Agotar límite de key1
        for _ in range(2):
            await rate_limit(key1, limit=2, window_seconds=60)

        # key2 aún puede hacer solicitudes
        await rate_limit(key2, limit=2, window_seconds=60)  # No debe fallar


# =============================================================================
# Tests para security functions
# =============================================================================


class TestSecurityFunctions:
    """Tests para funciones de seguridad."""

    def test_access_token_creation(self):
        """Verificar creación de access token."""
        from app.core.security import create_access_token

        data = {"sub": str(uuid4()), "role": "student"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20

    def test_access_token_decode(self):
        """Verificar decodificación de access token."""
        from app.core.security import create_access_token, decode_access_token

        user_id = str(uuid4())
        data = {"sub": user_id, "role": "student"}
        token = create_access_token(data)

        decoded = decode_access_token(token)

        assert decoded is not None
        assert str(decoded.user_id) == user_id
        assert decoded.role == "student"

    def test_access_token_invalid_returns_none(self):
        """Verificar que token inválido retorna None."""
        from app.core.security import decode_access_token

        result = decode_access_token("invalid_token_here")

        assert result is None

    def test_verify_password_mocked(self):
        """Test verify_password con mock."""
        from app.core.security import verify_password

        # Mock del contexto de password
        with patch('app.core.security.pwd_context.verify',
                   return_value=True):
            assert verify_password("pass", "hash") is True

        with patch('app.core.security.pwd_context.verify',
                   return_value=False):
            assert verify_password("wrong", "hash") is False

    def test_get_password_hash_mocked(self):
        """Test get_password_hash con mock."""
        from app.core.security import get_password_hash

        with patch('app.core.security.pwd_context.hash',
                   return_value="$2b$12$hashedvalue"):
            result = get_password_hash("password")
            assert result == "$2b$12$hashedvalue"


# =============================================================================
# Tests para TokenData model
# =============================================================================


class TestTokenDataModel:
    """Tests para modelo TokenData."""

    def test_token_data_creation(self):
        """Crear TokenData con todos los campos."""
        from app.core.security import TokenData

        user_id = uuid4()
        token_data = TokenData(
            user_id=user_id,
            email="test@example.com",
            role="student",
        )

        assert token_data.user_id == user_id
        assert token_data.email == "test@example.com"
        assert token_data.role == "student"

    def test_token_data_optional_fields(self):
        """TokenData funciona con campos opcionales."""
        from app.core.security import TokenData

        token_data = TokenData()

        assert token_data.user_id is None
        assert token_data.email is None
        assert token_data.role is None


# =============================================================================
# Tests para Token model
# =============================================================================


class TestTokenModel:
    """Tests para modelo Token."""

    def test_token_creation(self):
        """Crear Token con access_token."""
        from app.core.security import Token

        token = Token(access_token="test_token_123")

        assert token.access_token == "test_token_123"
        assert token.token_type == "bearer"

    def test_token_custom_type(self):
        """Crear Token con tipo personalizado."""
        from app.core.security import Token

        token = Token(access_token="test", token_type="custom")

        assert token.token_type == "custom"


# =============================================================================
# Tests para database functions
# =============================================================================


class TestDatabaseFunctions:
    """Tests para funciones de base de datos."""

    def test_database_url_construction(self):
        """Verificar construcción de URL de base de datos."""
        from app.core.config import get_settings

        settings = get_settings()

        # Debe tener URL de base de datos
        assert hasattr(settings, 'database_url')
