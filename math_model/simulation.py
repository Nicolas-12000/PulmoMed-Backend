"""
SimulationRunner - Ejecutor de simulaciones con integración al backend
"""
import asyncio
import httpx
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from .patient_profile import PatientProfile, DietType
from .tumor_growth_model import TumorGrowthModel
from .treatments import TreatmentStrategy, get_treatment


@dataclass
class SimulationResult:
    """Resultado de una simulación"""

    # Datos del paciente
    patient: PatientProfile

    # Estado inicial
    initial_volume: float

    # Estado final
    final_volume: float
    final_sensitive: float
    final_resistant: float

    # Simulación
    days_simulated: int
    treatment_name: str
    final_stage: str

    # Historial
    daily_states: List[Dict[str, float]] = field(default_factory=list)

    # Respuestas del backend (si se consultó)
    backend_responses: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    simulation_time_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Serializa resultado"""
        return {
            "patient": self.patient.to_dict(),
            "initial_volume": self.initial_volume,
            "final_volume": self.final_volume,
            "final_sensitive": self.final_sensitive,
            "final_resistant": self.final_resistant,
            "days_simulated": self.days_simulated,
            "treatment_name": self.treatment_name,
            "final_stage": self.final_stage,
            "daily_states": self.daily_states,
            "backend_responses": self.backend_responses,
            "simulation_time_ms": self.simulation_time_ms,
            "timestamp": self.timestamp,
        }


class SimulationRunner:
    """
    Ejecutor de simulaciones con integración al backend PulmoMed

    Permite:
    - Simular crecimiento tumoral con modelo matemático
    - Consultar al profesor IA en puntos clave
    - Validar respuestas del backend
    - Generar reportes de simulación
    """

    def __init__(
        self,
        backend_url: str = "http://localhost:8000",
        timeout: float = 30.0
    ):
        """
        Constructor

        Args:
            backend_url: URL del backend PulmoMed
            timeout: Timeout para requests HTTP
        """
        self.backend_url = backend_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Obtiene cliente HTTP (lazy init)"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.backend_url,
                timeout=self.timeout,
            )
        return self._client

    async def close(self):
        """Cierra el cliente HTTP"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def check_backend_health(self) -> Dict[str, Any]:
        """
        Verifica que el backend esté funcionando

        Returns:
            Respuesta del health check
        """
        client = await self._get_client()
        try:
            response = await client.get("/api/v1/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def consult_professor(self, state: dict) -> Dict[str, Any]:
        """
        Consulta al profesor IA con el estado actual

        Args:
            state: Estado de simulación (dict del TumorGrowthModel)

        Returns:
            Respuesta del profesor IA
        """
        client = await self._get_client()

        # Mapear nombres de campos si es necesario
        payload = {
            "age": state.get("age", 60),
            "is_smoker": state.get("is_smoker", False),
            "pack_years": state.get("pack_years", 0),
            "has_adequate_diet": state.get("has_adequate_diet", True),
            "sensitive_tumor_volume": state.get("sensitive_tumor_volume", 1.0),
            "resistant_tumor_volume": state.get("resistant_tumor_volume", 0.0),
            "active_treatment": state.get("active_treatment", "none"),
            "current_day": state.get("current_day", 0),
        }

        try:
            response = await client.post(
                "/api/v1/consultar_profesor",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": True,
                "status_code": e.response.status_code,
                "detail": e.response.text,
            }
        except Exception as e:
            return {"error": True, "detail": str(e)}

    async def run_simulation(
        self,
        patient: PatientProfile,
        initial_volume: float,
        days: int = 90,
        treatment: Optional[TreatmentStrategy] = None,
        treatment_start_day: int = 0,
        consult_interval: int = 30,  # Consultar cada N días
        initial_resistant_fraction: float = 0.0,
    ) -> SimulationResult:
        """
        Ejecuta una simulación completa

        Args:
            patient: Perfil del paciente
            initial_volume: Volumen inicial del tumor (cm³)
            days: Días a simular
            treatment: Estrategia de tratamiento (None = sin tratamiento)
            treatment_start_day: Día en que inicia el tratamiento
            consult_interval: Intervalo de consulta al profesor IA
            initial_resistant_fraction: Fracción inicial de células resistentes

        Returns:
            SimulationResult con todos los datos
        """
        import time
        start_time = time.perf_counter()

        # Calcular volúmenes iniciales
        sensitive = initial_volume * (1 - initial_resistant_fraction)
        resistant = initial_volume * initial_resistant_fraction

        # Crear modelo
        model = TumorGrowthModel(
            patient=patient,
            initial_sensitive_volume=sensitive,
            initial_resistant_volume=resistant,
        )

        daily_states = []
        backend_responses = []

        # Simular día a día
        for day in range(1, days + 1):
            # Aplicar tratamiento si corresponde
            if treatment and day == treatment_start_day:
                model.set_treatment(treatment)

            # Avanzar simulación
            model.simulate_step(1.0)

            # Guardar estado diario
            state = model.get_state_dict()
            daily_states.append({
                "day": day,
                "sensitive": model.sensitive_cells,
                "resistant": model.resistant_cells,
                "total": model.total_volume,
                "stage": model.get_approximate_stage(),
            })

            # Consultar profesor en intervalos
            if consult_interval > 0 and day % consult_interval == 0:
                response = await self.consult_professor(state)
                backend_responses.append({
                    "day": day,
                    "state": state,
                    "response": response,
                })

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return SimulationResult(
            patient=patient,
            initial_volume=initial_volume,
            final_volume=model.total_volume,
            final_sensitive=model.sensitive_cells,
            final_resistant=model.resistant_cells,
            days_simulated=days,
            treatment_name=treatment.name if treatment else "Ninguno",
            final_stage=model.get_approximate_stage(),
            daily_states=daily_states,
            backend_responses=backend_responses,
            simulation_time_ms=elapsed_ms,
        )

    def run_simulation_sync(
        self,
        patient: PatientProfile,
        initial_volume: float,
        days: int = 90,
        treatment: Optional[TreatmentStrategy] = None,
        treatment_start_day: int = 0,
        consult_interval: int = 30,
        initial_resistant_fraction: float = 0.0,
    ) -> SimulationResult:
        """
        Versión síncrona de run_simulation
        """
        return asyncio.run(self.run_simulation(
            patient=patient,
            initial_volume=initial_volume,
            days=days,
            treatment=treatment,
            treatment_start_day=treatment_start_day,
            consult_interval=consult_interval,
            initial_resistant_fraction=initial_resistant_fraction,
        ))


# === Funciones de conveniencia ===

def create_sample_patient(
    scenario: str = "typical"
) -> PatientProfile:
    """
    Crea un paciente de ejemplo para pruebas

    Args:
        scenario: "typical", "young_healthy", "elderly_smoker", "high_risk"

    Returns:
        PatientProfile configurado
    """
    scenarios = {
        "typical": PatientProfile(
            age=62,
            is_smoker=False,
            pack_years=0,
            diet=DietType.NORMAL,
            genetic_factor=1.0,
        ),
        "young_healthy": PatientProfile(
            age=35,
            is_smoker=False,
            pack_years=0,
            diet=DietType.HEALTHY,
            genetic_factor=0.9,
        ),
        "elderly_smoker": PatientProfile(
            age=72,
            is_smoker=True,
            pack_years=45,
            diet=DietType.POOR,
            genetic_factor=1.1,
        ),
        "high_risk": PatientProfile(
            age=68,
            is_smoker=True,
            pack_years=60,
            diet=DietType.POOR,
            genetic_factor=1.3,
        ),
    }

    return scenarios.get(scenario, scenarios["typical"])


async def quick_simulation_test(
    backend_url: str = "http://localhost:8000"
) -> Dict[str, Any]:
    """
    Ejecuta una simulación rápida de prueba

    Args:
        backend_url: URL del backend

    Returns:
        Resumen de la simulación
    """
    runner = SimulationRunner(backend_url)

    try:
        # Verificar backend
        health = await runner.check_backend_health()
        if health.get("status") != "ok":
            return {"error": "Backend no disponible", "health": health}

        # Crear paciente típico
        patient = create_sample_patient("elderly_smoker")

        # Crear tratamiento
        treatment = get_treatment("chemotherapy")

        # Simular 90 días
        result = await runner.run_simulation(
            patient=patient,
            initial_volume=5.0,  # 5 cm³ inicial
            days=90,
            treatment=treatment,
            treatment_start_day=7,
            consult_interval=30,
        )

        return {
            "success": True,
            "patient": patient.to_dict(),
            "initial_volume": result.initial_volume,
            "final_volume": result.final_volume,
            "days": result.days_simulated,
            "treatment": result.treatment_name,
            "final_stage": result.final_stage,
            "backend_consultations": len(result.backend_responses),
            "simulation_time_ms": result.simulation_time_ms,
        }
    finally:
        await runner.close()


# Para ejecutar directamente
if __name__ == "__main__":
    import json

    result = asyncio.run(quick_simulation_test())
    print(json.dumps(result, indent=2, default=str))
