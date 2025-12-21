"""
Domain Models - LungCancerVR Backend
Modelos Pydantic para validación y serialización (SOLID: SRP)
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


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
