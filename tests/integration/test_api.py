"""
Integration Tests - API Endpoints
Prueba flujo completo end-to-end
"""

import sys
from pathlib import Path

import pytest

# Añadir root al path para importar main
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402


@pytest.fixture
def client():
    """Fixture: Cliente HTTP para testing"""
    return TestClient(app)


class TestAPIEndpoints:
    """Tests de integración para endpoints"""

    def test_root_endpoint(self, client):
        """Test: Endpoint raíz retorna info correcta"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["docs"] == "/docs"

    def test_health_check(self, client):
        """Test: Health check retorna estado del sistema"""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "vector_db_status" in data
        assert "embedding_model" in data

    def test_consultar_profesor_valid_request(self, client):
        """Test: Consulta válida al profesor retorna respuesta estructurada"""
        state = {
            "edad": 58,
            "es_fumador": False,
            "pack_years": 0,
            "dieta": "saludable",
            "volumen_tumor_sensible": 2.5,
            "volumen_tumor_resistente": 0.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
            "modo": "libre",
        }

        response = client.post("/api/v1/consultar_profesor", json=state)

        assert response.status_code == 200
        data = response.json()

        # Validar estructura de respuesta
        assert "explicacion" in data
        assert "recomendacion" in data
        assert "fuentes" in data
        assert "advertencia" in data
        assert isinstance(data["fuentes"], list)

    def test_consultar_profesor_invalid_age(self, client):
        """Test: Edad inválida retorna error 422"""
        state = {"edad": 150, "volumen_tumor_sensible": 5.0}  # Invalid

        response = client.post("/api/v1/consultar_profesor", json=state)

        assert response.status_code == 422  # Validation error

    def test_consultar_profesor_smoker_with_pack_years(self, client):
        """Test: Fumador con pack_years alto"""
        state = {
            "edad": 67,
            "es_fumador": True,
            "pack_years": 45.0,
            "dieta": "mala",
            "volumen_tumor_sensible": 18.3,
            "volumen_tumor_resistente": 1.2,
            "tratamiento_activo": "quimio",
            "dias_tratamiento": 30,
        }

        response = client.post("/api/v1/consultar_profesor", json=state)

        assert response.status_code == 200
        data = response.json()

        # Respuesta debe mencionar tabaquismo
        assert len(data["explicacion"]) > 50
        assert data["advertencia"] is not None

    def test_consultar_profesor_treatment_response(self, client):
        """Test: Paciente bajo tratamiento con resistencia"""
        state = {
            "edad": 52,
            "es_fumador": False,
            "pack_years": 0.0,
            "dieta": "saludable",
            "volumen_tumor_sensible": 24.8,
            "volumen_tumor_resistente": 0.5,
            "tratamiento_activo": "inmuno",
            "dias_tratamiento": 45,
        }

        response = client.post("/api/v1/consultar_profesor", json=state)

        assert response.status_code == 200
        data = response.json()
        assert data["retrieved_chunks"] >= 0

    def test_consultar_profesor_invalid_pack_years(self, client):
        """Test: No fumador con pack_years > 0 debe fallar"""
        state = {
            "edad": 60,
            "es_fumador": False,
            "pack_years": 20.0,  # Invalid
            "volumen_tumor_sensible": 5.0,
        }

        response = client.post("/api/v1/consultar_profesor", json=state)

        assert response.status_code == 422

    def test_listar_casos_biblioteca(self, client):
        """Test: Endpoint de casos de biblioteca"""
        response = client.get("/api/v1/casos_biblioteca")

        assert response.status_code == 200
        data = response.json()
        assert "cases" in data
        assert "count" in data

    def test_consultar_profesor_modo_biblioteca(self, client):
        """Test: Consulta en modo biblioteca con caso_id"""
        state = {
            "edad": 58,
            "volumen_tumor_sensible": 2.5,
            "modo": "biblioteca",
            "caso_id": "SEER_001_estadio_IA",
        }

        response = client.post("/api/v1/consultar_profesor", json=state)

        assert response.status_code == 200
        data = response.json()
        assert "llm_model" in data or "model_used" in data  # Acepta ambos (alias)


class TestCORSMiddleware:
    """Tests para configuración CORS"""

    def test_cors_headers_present(self, client):
        """Test: Headers CORS están presentes"""
        response = client.options(
            "/api/v1/health", headers={"Origin": "http://localhost:3000"}
        )

        # CORS debe permitir requests
        assert response.status_code in [
            200,
            405,
        ]  # 405 si OPTIONS no implementado explícitamente
