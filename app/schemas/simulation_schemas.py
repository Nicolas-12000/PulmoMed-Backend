"""Contratos HTTP para ejecutar el modelo matemático desde Unity."""

from typing import Literal

from pydantic import BaseModel, Field


class LungSimulationRequest(BaseModel):
    edad: int = Field(default=60, ge=18, le=100)
    es_fumador: bool = False
    pack_years: float = Field(default=0.0, ge=0, le=150)
    dieta: Literal["saludable", "normal", "mala"] = "normal"
    factor_genetico: float = Field(default=1.0, ge=0.5, le=2.0)
    volumen_inicial_sensible: float = Field(default=0.35, gt=0, le=100)
    volumen_inicial_resistente: float = Field(default=0.01, ge=0, le=100)
    tratamiento: Literal["ninguno", "quimio", "radio", "inmuno", "cirugia"] = "ninguno"
    dias: int = Field(default=180, ge=1, le=730)
    intervalo_muestra: int = Field(default=1, ge=1, le=30)
    dia_inicio_tratamiento: int = Field(default=0, ge=0, le=730)


class LungSimulationFrame(BaseModel):
    dia: int
    volumen_sensible: float
    volumen_resistente: float
    volumen_total: float
    fraccion_resistente: float
    progreso: float
    estadio: str


class LungSimulationResponse(BaseModel):
    simulation_id: str
    modelo: str
    dias_simulados: int
    capacidad_carga: float
    volumen_inicial: float
    volumen_final: float
    estadio_final: str
    tiempo_ms: float = 0.0
    frames: list[LungSimulationFrame]
