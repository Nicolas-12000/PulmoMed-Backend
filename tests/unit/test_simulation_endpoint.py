"""Tests de la trayectoria tumoral que Unity reproduce."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.simulation_endpoint import router
from app.schemas.simulation_schemas import LungSimulationRequest
from app.services.simulation_service import run_lung_trajectory

app = FastAPI()
app.include_router(router, prefix="/api/v1")
client = TestClient(app)


def test_run_lung_trajectory_grows_without_treatment():
    request = LungSimulationRequest(
        edad=62,
        es_fumador=True,
        pack_years=30,
        dieta="mala",
        dias=30,
        intervalo_muestra=5,
        tratamiento="ninguno",
    )
    result = run_lung_trajectory(request)
    assert result.dias_simulados == 30
    assert result.volumen_final >= result.volumen_inicial
    assert result.frames[0].dia == 0
    assert result.frames[-1].dia == 30
    assert result.tiempo_ms >= 0


def test_chemotherapy_reduces_volume_vs_untreated():
    untreated = run_lung_trajectory(
        LungSimulationRequest(dias=60, intervalo_muestra=10, tratamiento="ninguno")
    )
    treated = run_lung_trajectory(
        LungSimulationRequest(dias=60, intervalo_muestra=10, tratamiento="quimio")
    )
    assert treated.volumen_final < untreated.volumen_final


def test_simulation_endpoint_returns_unity_contract():
    response = client.post(
        "/api/v1/simulation/run",
        json={
            "edad": 58,
            "es_fumador": False,
            "pack_years": 15,
            "dieta": "saludable",
            "tratamiento": "ninguno",
            "dias": 10,
            "intervalo_muestra": 2,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["modelo"].startswith("Gompertz")
    assert payload["dias_simulados"] == 10
    assert payload["frames"][0]["dia"] == 0
    assert "volumen_total" in payload["frames"][0]
    assert "estadio" in payload["frames"][0]


def test_teacher_state_endpoint():
    response = client.post(
        "/api/v1/simulation/teacher-state",
        json={
            "edad": 60,
            "tratamiento": "quimio",
            "dias": 15,
            "dia_inicio_tratamiento": 5,
            "volumen_inicial_sensible": 2.0,
            "volumen_inicial_resistente": 0.05,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["edad"] == 60
    assert payload["tratamiento_activo"] == "quimio"
    assert payload["volumen_tumor_sensible"] > 0


def test_simulation_endpoint_rejects_invalid_diet():
    response = client.post(
        "/api/v1/simulation/run",
        json={"dieta": "hipercalorica", "dias": 5},
    )
    assert response.status_code == 422


def test_delayed_treatment_and_invalid_service_values():
    delayed = run_lung_trajectory(
        LungSimulationRequest(
            dias=20,
            intervalo_muestra=5,
            tratamiento="quimio",
            dia_inicio_tratamiento=10,
        )
    )
    assert delayed.frames[-1].dia == 20

    invalid_diet = LungSimulationRequest.model_construct(dieta="rara", tratamiento="ninguno", dias=1)
    try:
        run_lung_trajectory(invalid_diet)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Dieta" in str(exc)

    invalid_treatment = LungSimulationRequest.model_construct(
        dieta="normal", tratamiento="homeopatia", dias=1
    )
    try:
        run_lung_trajectory(invalid_treatment)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Tratamiento" in str(exc)
