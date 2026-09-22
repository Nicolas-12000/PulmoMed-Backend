"""Servidor ligero para probar la simulación pulmonar desde Unity."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.simulation_endpoint import router as simulation_router


app = FastAPI(
    title="PulmoMed - Simulación tumoral para Unity",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulation_router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "pulmomed-simulation"}

