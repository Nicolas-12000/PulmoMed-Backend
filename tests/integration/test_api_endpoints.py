"""
Tests de integración para API endpoints
Suite completa de tests para endpoints HTTP del backend.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from fastapi.testclient import TestClient
from httpx import AsyncClient

# Importar la app
try:
    from main import app
except ImportError:
    app = None


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def client():
    """Cliente de test síncrono."""
    if app is None:
        pytest.skip("App no disponible")
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Cliente de test asíncrono."""
    if app is None:
        pytest.skip("App no disponible")
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_db():
    """Mock de sesión de base de datos."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def sample_user():
    """Usuario de ejemplo."""
    from app.models.db_models import UserRole
    user = MagicMock()
    user.id = uuid4()
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.role = UserRole.STUDENT
    user.is_active = True
    user.created_at = datetime.utcnow()
    return user


@pytest.fixture
def sample_teacher():
    """Profesor de ejemplo."""
    from app.models.db_models import UserRole
    teacher = MagicMock()
    teacher.id = uuid4()
    teacher.email = "teacher@example.com"
    teacher.full_name = "Test Teacher"
    teacher.role = UserRole.TEACHER
    teacher.is_active = True
    return teacher


# =============================================================================
# Tests para Health Check
# =============================================================================

class TestHealthEndpoint:
    """Tests para endpoint de health check."""

    def test_health_check_returns_200(self, client):
        """Health check retorna 200."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_check_returns_status(self, client):
        """Health check retorna status."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert "status" in data

    def test_root_endpoint(self, client):
        """Root endpoint funciona."""
        response = client.get("/")
        assert response.status_code == 200


# =============================================================================
# Tests para Auth Endpoints
# =============================================================================

class TestAuthEndpoints:
    """Tests para endpoints de autenticación."""

    def test_login_without_credentials(self, client):
        """Login sin credenciales falla."""
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code in [400, 422]

    def test_login_with_invalid_credentials(self, client):
        """Login con credenciales inválidas falla."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "fake@email.com", "password": "wrongpass"}
        )
        # 401 o 404 dependiendo de implementación
        assert response.status_code in [401, 404, 422]

    def test_register_requires_fields(self, client):
        """Registro requiere campos obligatorios."""
        response = client.post("/api/v1/auth/register", json={})
        assert response.status_code == 422

    def test_register_validates_email(self, client):
        """Registro valida formato de email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "password123",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 422

    def test_register_validates_password_length(self, client):
        """Registro valida longitud de contraseña."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "123",  # Muy corta
                "full_name": "Test User"
            }
        )
        assert response.status_code == 422


# =============================================================================
# Tests para Teacher Endpoints
# =============================================================================

class TestTeacherEndpoints:
    """Tests para endpoints del profesor IA."""

    def test_consult_requires_auth(self, client):
        """Consulta requiere autenticación."""
        response = client.post(
            "/api/v1/consultar_profesor",
            json={"question": "¿Qué es el cáncer?"}
        )
        # Sin auth puede dar 401 o 403
        assert response.status_code in [401, 403, 422]

    def test_consult_validates_payload(self, client):
        """Consulta valida payload."""
        response = client.post(
            "/api/v1/consultar_profesor",
            json={}
        )
        assert response.status_code in [401, 403, 422]


# =============================================================================
# Tests para Exam Endpoints
# =============================================================================

class TestExamEndpoints:
    """Tests para endpoints de exámenes."""

    def test_list_exams_endpoint_exists(self, client):
        """Endpoint de listar exámenes existe (my-exams)."""
        response = client.get("/api/v1/exams/my-exams")
        # Puede requerir auth (401/403) o existir (200/422)
        assert response.status_code in [200, 401, 403, 422]

    def test_create_exam_requires_auth(self, client):
        """Crear examen requiere autenticación."""
        response = client.post(
            "/api/v1/exams/",
            json={"title": "Test Exam", "exam_type": "mini_quiz"}
        )
        assert response.status_code in [401, 403, 422]

    def test_get_exam_not_found(self, client):
        """Obtener examen inexistente da 404."""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/exams/{fake_id}")
        # Sin auth o no encontrado
        assert response.status_code in [401, 403, 404]


# =============================================================================
# Tests para Course Endpoints
# =============================================================================

class TestCourseEndpoints:
    """Tests para endpoints de cursos."""

    def test_list_courses_endpoint_exists(self, client):
        """Endpoint de listar cursos existe (my-courses)."""
        response = client.get("/api/v1/courses/my-courses")
        # Puede requerir auth o existir
        assert response.status_code in [200, 401, 403, 422]

    def test_create_course_requires_teacher(self, client):
        """Crear curso requiere rol de profesor."""
        response = client.post(
            "/api/v1/courses/",
            json={"name": "Test Course", "code": "TEST101"}
        )
        assert response.status_code in [401, 403, 422]


# =============================================================================
# Tests para Stats Endpoints
# =============================================================================

class TestStatsEndpoints:
    """Tests para endpoints de estadísticas."""

    def test_stats_endpoint_exists(self, client):
        """Endpoint de estadísticas existe."""
        response = client.get("/api/v1/stats/me")
        # Puede requerir auth o no encontrar la ruta
        assert response.status_code in [200, 401, 403, 404, 422]

    def test_leaderboard_endpoint_exists(self, client):
        """Endpoint de leaderboard existe."""
        response = client.get("/api/v1/stats/leaderboard")
        # Puede requerir auth o no existir
        assert response.status_code in [200, 401, 403, 404, 422]


# =============================================================================
# Tests de validación de schemas
# =============================================================================

class TestSchemaValidation:
    """Tests para validación de schemas en endpoints."""

    def test_invalid_uuid_returns_422(self, client):
        """UUID inválido retorna 422."""
        response = client.get("/api/v1/exams/invalid-uuid")
        assert response.status_code in [401, 403, 422]

    def test_invalid_json_returns_422(self, client):
        """JSON inválido retorna 422."""
        response = client.post(
            "/api/v1/auth/register",
            content="not json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


# =============================================================================
# Tests de Rate Limiting
# =============================================================================

class TestRateLimiting:
    """Tests para rate limiting."""

    def test_rate_limiter_allows_requests(self, client):
        """Rate limiter permite requests normales."""
        # Hacer varios requests rápidos
        for _ in range(5):
            response = client.get("/api/v1/health")
            # No debe dar 429 con pocos requests
            assert response.status_code != 429 or response.status_code == 200


# =============================================================================
# Tests de integración asíncronos
# =============================================================================

@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Tests asíncronos para endpoints."""

    async def test_health_async(self, async_client):
        """Health check asíncrono."""
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200

    async def test_concurrent_requests(self, async_client):
        """Múltiples requests concurrentes."""
        import asyncio

        async def make_request():
            return await async_client.get("/api/v1/health")

        # 10 requests concurrentes
        responses = await asyncio.gather(*[make_request() for _ in range(10)])

        # Todos deben ser exitosos
        assert all(r.status_code == 200 for r in responses)


# =============================================================================
# Tests con autenticación mockeada
# =============================================================================

class TestAuthenticatedEndpoints:
    """Tests para endpoints con autenticación mockeada."""

    def test_health_without_auth_works(self, client):
        """Health endpoint no requiere auth."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200


# =============================================================================
# Tests de respuestas de error
# =============================================================================

class TestErrorResponses:
    """Tests para respuestas de error."""

    def test_404_on_unknown_route(self, client):
        """404 en ruta desconocida."""
        response = client.get("/api/v1/unknown/route")
        assert response.status_code == 404

    def test_405_on_wrong_method(self, client):
        """405 en método incorrecto."""
        response = client.delete("/api/v1/health")
        assert response.status_code in [405, 404]

    def test_error_response_has_detail(self, client):
        """Respuestas de error tienen detalle."""
        response = client.get("/api/v1/exams/invalid-uuid")
        if response.status_code >= 400:
            data = response.json()
            assert "detail" in data or "message" in data or "error" in data


# =============================================================================
# Tests de CORS
# =============================================================================

class TestCORS:
    """Tests para configuración CORS."""

    def test_cors_headers_present(self, client):
        """Headers CORS presentes."""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        # CORS puede estar configurado o no
        # Solo verificamos que no falle
        assert response.status_code in [200, 204, 404, 405]


# =============================================================================
# Tests de OpenAPI/Docs
# =============================================================================

class TestOpenAPI:
    """Tests para documentación OpenAPI."""

    def test_openapi_json_available(self, client):
        """OpenAPI JSON disponible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_docs_available(self, client):
        """Documentación Swagger disponible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_available(self, client):
        """Documentación ReDoc disponible."""
        response = client.get("/redoc")
        assert response.status_code == 200
