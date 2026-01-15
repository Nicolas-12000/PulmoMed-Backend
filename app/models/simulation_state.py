"""
Domain Models - LungCancerVR Backend
Modelos Pydantic para validación y serialización (SOLID: SRP)
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LungState(str, Enum):
    SANO = "sano"
    EN_RIESGO = "en_riesgo"
    ESTABLE = "estable"
    PROGRESANDO = "progresando"
    CRITICO = "critico"
    TERMINAL = "terminal"


class SimulationState(BaseModel):
    """
    Estado de la simulación enviado desde Unity
    Representa el snapshot del paciente en un momento dado
    """

    # Datos del Paciente
    age: int = Field(..., ge=18, le=100, description="Edad del paciente (18-100)", alias="edad")
    is_smoker: bool = Field(default=False, description="Fumador activo o ex-fumador", alias="es_fumador")
    pack_years: float = Field(
        default=0.0, ge=0, le=150, description="Paquetes-año acumulados", alias="pack_years"
    )
    # Tiempo desde último cambio de hábito (días)
    days_since_smoking_change: int = Field(default=0, ge=0, alias="dias_desde_cambio")

    # Estado sintético del pulmón (se calcula o se puede fijar)
    lung_state: LungState | None = Field(default=None)
    diet: Literal["saludable", "normal", "mala"] = Field(default="normal", alias="dieta")

    # Estado del Tumor (valores de la simulación matemática)
    sensitive_tumor_volume: float = Field(
        ..., ge=0, description="Volumen células sensibles (cm³)", alias="volumen_tumor_sensible"
    )
    resistant_tumor_volume: float = Field(
        default=0.0, ge=0, description="Volumen células resistentes (cm³)", alias="volumen_tumor_resistente"
    )

    # Tratamiento Actual
    active_treatment: Literal["ninguno", "quimio", "radio", "inmuno"] = Field(
        default="ninguno", alias="tratamiento_activo"
    )
    treatment_days: int = Field(
        default=0, ge=0, description="Días acumulados de tratamiento", alias="dias_tratamiento"
    )

    # Contexto de Modo
    mode: Literal["libre", "biblioteca"] = Field(default="libre", alias="modo")
    case_id: str | None = Field(
        default=None, description="ID del caso si modo=biblioteca", alias="caso_id"
    )

    model_config = {"populate_by_name": True}

    @field_validator("pack_years")
    @classmethod
    def validate_pack_years(cls, v: float, info) -> float:
        """Validación: pack_years > 0 solo si is_smoker"""
        if not info.data.get("is_smoker", False) and v > 0:
            raise ValueError("pack_years debe ser 0 si no es fumador")
        return v

    @property
    def total_volume(self) -> float:
        """Volumen total del tumor"""
        return self.sensitive_tumor_volume + self.resistant_tumor_volume

    def compute_risk_score(self) -> float:
        """Calcula score de riesgo combinando edad, pack_years y volumen tumoral.

        Score normalizado 0..1; mayor = peor pronóstico.
        """
        from app.core.config import get_settings
        settings = get_settings()
        
        # Factor edad (18-100 -> 0..1)
        age_range = settings.max_patient_age - settings.min_patient_age
        age_factor = max(0.0, min(1.0, (self.age - settings.min_patient_age) / age_range))
        
        # Factor tabaquismo (pack-years normalizado)
        pack_factor = min(1.0, self.pack_years / settings.max_pack_years)
        
        # Factor volumen tumoral
        vol_factor = min(1.0, self.total_volume / settings.max_tumor_volume)
        
        # Combinación ponderada
        return 0.4 * age_factor + 0.4 * pack_factor + 0.2 * vol_factor

    def update_lung_state(self) -> LungState:
        """Update and return a computed `lung_state` from current values.

        Rules (simple heuristic):
        - If volumen_total == 0 -> SANO
        - If risk_score < 0.2 -> EN_RIESGO
        - If vol < 3.0 -> ESTABLE
        - If vol between 3..20 -> PROGRESANDO
        - If vol between 20..60 -> CRITICO
        - else -> TERMINAL
        """
        vol = self.total_volume
        if vol <= 0.0:
            state = LungState.SANO
        else:
            score = self.compute_risk_score()
            if score < 0.2:
                state = LungState.EN_RIESGO
            elif vol < 3.0:
                state = LungState.ESTABLE
            elif vol < 20.0:
                state = LungState.PROGRESANDO
            elif vol < 60.0:
                state = LungState.CRITICO
            else:
                state = LungState.TERMINAL

        self.lung_state = state
        return state

    # --- Smoking behavior helpers ---
    def start_smoking(self, cigarettes_per_day: int = 20) -> None:
        """Mark the patient as smoking; future simulation steps can increase `pack_years`.

        This method sets `es_fumador` and notes the change time counter reset.
        """
        self.is_smoker = True
        self.days_since_smoking_change = 0

    def stop_smoking(self) -> None:
        """Mark the patient as having stopped smoking; resets the change counter."""
        self.is_smoker = False
        self.days_since_smoking_change = 0

    def advance_time_and_accumulate_smoking(self, days: int, cigarettes_per_day: int = 20) -> None:
        """Avanza el tiempo en días; si el paciente fuma, acumula pack-years.

        pack-years aproximado como: (cigarrillos_por_dia / 20) * (dias / 365)
        """
        from app.core.config import get_settings
        
        if days <= 0:
            return
        self.days_since_smoking_change += days
        if self.is_smoker:
            added_years = (cigarettes_per_day / 20.0) * (days / 365.0)
            max_pack = get_settings().max_pack_years
            self.pack_years = min(max_pack, self.pack_years + added_years)

    @property
    def approx_stage(self) -> str:
        """
        Estimación del estadio TNM basado en volumen.
        Simplificación educativa (no diagnóstico real).
        """
        from app.core.config import get_settings
        settings = get_settings()
        
        vol = self.total_volume
        if vol < settings.stage_ia_max_volume:
            return "IA (T1a)"
        elif vol < settings.stage_ib_max_volume:
            return "IB (T2a)"
        elif vol < settings.stage_iia_max_volume:
            return "IIA (T2b)"
        elif vol < settings.stage_iib_max_volume:
            return "IIB (T3)"
        else:
            return "IIIA+ (T4 o avanzado)"


class TeacherResponse(BaseModel):
    """
    Respuesta del IA "Profesor" al Unity Client
    Contiene feedback educativo basado en RAG
    """

    explanation: str = Field(..., description="Explicación médica del estado actual")
    recommendation: str = Field(..., description="Recomendación terapéutica educativa")
    sources: list[str] = Field(
        default_factory=list, description="Referencias médicas (NCCN, estudios)"
    )
    warning: str | None = Field(
        default=None, description="Disclaimer educativo si aplica"
    )

    # Metadata (opcional, para debugging)
    retrieved_chunks: int = Field(
        default=0, description="Número de chunks RAG recuperados"
    )
    llm_model: str = Field(
        default="mock", description="Modelo LLM usado", alias="model_used"
    )

    model_config = {"protected_namespaces": ()}


class LibraryCase(BaseModel):
    """
    Caso predefinido para Modo Biblioteca
    Basado en estadísticas SEER y guías NCCN
    """

    case_id: str = Field(..., description="Identificador único del caso", alias="caso_id")
    title: str = Field(..., description="Título descriptivo del caso", alias="titulo")
    description: str = Field(..., description="Historia clínica resumida", alias="descripcion")

    # Parámetros del paciente
    age: int = Field(..., alias="edad")
    is_smoker: bool = Field(..., alias="es_fumador")
    pack_years: float = Field(..., alias="pack_years")
    diet: Literal["saludable", "normal", "mala"] = Field(..., alias="dieta")

    # Estado inicial del tumor
    initial_sensitive_volume: float = Field(..., alias="volumen_inicial_sensible")
    initial_resistant_volume: float = Field(default=0.0, alias="volumen_inicial_resistente")

    # Contexto educativo
    learning_objectives: list[str] = Field(default_factory=list, alias="objetivos_aprendizaje")
    statistical_source: str = Field(..., description="Referencia SEER/NCCN", alias="fuente_estadistica")

    model_config = {"populate_by_name": True}


class HealthCheckResponse(BaseModel):
    """Response del endpoint de health check"""

    status: str
    version: str
    vector_db_status: str
    embedding_model: str
