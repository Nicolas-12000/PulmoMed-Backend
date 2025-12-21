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
    edad: int = Field(..., ge=18, le=100, description="Edad del paciente (18-100)")
    es_fumador: bool = Field(default=False, description="Fumador activo o ex-fumador")
    pack_years: float = Field(
        default=0.0, ge=0, le=150, description="Paquetes-año acumulados"
    )
    # Tiempo desde último cambio de hábito (días)
    dias_desde_cambio_tabaco: int = Field(default=0, ge=0)

    # Estado sintético del pulmón (se calcula o se puede fijar)
    lung_state: LungState | None = Field(default=None)
    dieta: Literal["saludable", "normal", "mala"] = Field(default="normal")

    # Estado del Tumor (valores de la simulación matemática)
    volumen_tumor_sensible: float = Field(
        ..., ge=0, description="Volumen células sensibles (cm³)"
    )
    volumen_tumor_resistente: float = Field(
        default=0.0, ge=0, description="Volumen células resistentes (cm³)"
    )

    # Tratamiento Actual
    tratamiento_activo: Literal["ninguno", "quimio", "radio", "inmuno"] = Field(
        default="ninguno"
    )
    dias_tratamiento: int = Field(
        default=0, ge=0, description="Días acumulados de tratamiento"
    )

    # Contexto de Modo
    modo: Literal["libre", "biblioteca"] = Field(default="libre")
    caso_id: str | None = Field(
        default=None, description="ID del caso si modo=biblioteca"
    )

    @field_validator("pack_years")
    @classmethod
    def validate_pack_years(cls, v: float, info) -> float:
        """Validación: pack_years > 0 solo si es_fumador"""
        if not info.data.get("es_fumador", False) and v > 0:
            raise ValueError("pack_years debe ser 0 si no es fumador")
        return v

    @property
    def volumen_total(self) -> float:
        """Volumen total del tumor"""
        return self.volumen_tumor_sensible + self.volumen_tumor_resistente

    def compute_risk_score(self) -> float:
        """Compute a simple risk score combining age and pack_years and tumor volume.

        Normalized 0..1 score; higher means worse.
        """
        # Age factor (18-100 -> 0..1)
        age_factor = max(0.0, min(1.0, (self.edad - 18) / (100 - 18)))
        # Pack-years normalized to 150
        pack_factor = min(1.0, self.pack_years / 150.0)
        # Volume factor: assume 0-100 maps to 0..1
        vol = self.volumen_total
        vol_factor = min(1.0, vol / 100.0)
        # Weighted combination
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
        vol = self.volumen_total
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
        self.es_fumador = True
        self.dias_desde_cambio_tabaco = 0

    def stop_smoking(self) -> None:
        """Mark the patient as having stopped smoking; resets the change counter."""
        self.es_fumador = False
        self.dias_desde_cambio_tabaco = 0

    def advance_time_and_accumulate_smoking(self, days: int, cigarettes_per_day: int = 20) -> None:
        """Advance time in days; if patient smokes, accumulate pack-years.

        pack-years approximated as: (cigarettes_per_day / 20) * (days / 365)
        """
        if days <= 0:
            return
        self.dias_desde_cambio_tabaco += days
        if self.es_fumador:
            added_years = (cigarettes_per_day / 20.0) * (days / 365.0)
            self.pack_years = min(150.0, self.pack_years + added_years)

    @property
    def estadio_aproximado(self) -> str:
        """
        Estimación del estadio TNM basado en volumen
        Simplificación educativa (no diagnóstico real)
        """
        vol = self.volumen_total
        if vol < 3.0:
            return "IA (T1a)"
        elif vol < 14.0:
            return "IB (T2a)"
        elif vol < 28.0:
            return "IIA (T2b)"
        elif vol < 65.0:
            return "IIB (T3)"
        else:
            return "IIIA+ (T4 o avanzado)"


class TeacherResponse(BaseModel):
    """
    Respuesta del IA "Profesor" al Unity Client
    Contiene feedback educativo basado en RAG
    """

    explicacion: str = Field(..., description="Explicación médica del estado actual")
    recomendacion: str = Field(..., description="Recomendación terapéutica educativa")
    fuentes: list[str] = Field(
        default_factory=list, description="Referencias médicas (NCCN, estudios)"
    )
    advertencia: str | None = Field(
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


class CasoBiblioteca(BaseModel):
    """
    Caso predefinido para Modo Biblioteca
    Basado en estadísticas SEER y guías NCCN
    """

    caso_id: str = Field(..., description="Identificador único del caso")
    titulo: str = Field(..., description="Título descriptivo del caso")
    descripcion: str = Field(..., description="Historia clínica resumida")

    # Parámetros del paciente
    edad: int
    es_fumador: bool
    pack_years: float
    dieta: Literal["saludable", "normal", "mala"]

    # Estado inicial del tumor
    volumen_inicial_sensible: float
    volumen_inicial_resistente: float = 0.0

    # Contexto educativo
    objetivos_aprendizaje: list[str] = Field(default_factory=list)
    fuente_estadistica: str = Field(..., description="Referencia SEER/NCCN")


class HealthCheckResponse(BaseModel):
    """Response del endpoint de health check"""

    status: str
    version: str
    vector_db_status: str
    embedding_model: str
