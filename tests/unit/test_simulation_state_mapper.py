from app.models.simulation_state import SimulationState
from app.schemas.simulation_schemas import LungSimulationFrame, LungSimulationRequest
from app.services.simulation_service import run_lung_trajectory
from app.services.simulation_state_mapper import teacher_state_from_lung


def test_teacher_state_matches_last_frame():
    request = LungSimulationRequest(
        edad=62,
        es_fumador=True,
        pack_years=20,
        dieta="mala",
        tratamiento="quimio",
        dias=45,
        dia_inicio_tratamiento=10,
        intervalo_muestra=5,
    )
    trajectory = run_lung_trajectory(request)
    frame = trajectory.frames[-1]

    state = teacher_state_from_lung(request, frame)
    assert isinstance(state, SimulationState)
    assert state.sensitive_tumor_volume == frame.volumen_sensible
    assert state.resistant_tumor_volume == frame.volumen_resistente
    assert state.active_treatment == "quimio"
    assert state.treatment_days == frame.dia - 10


def test_teacher_state_no_treatment_days():
    request = LungSimulationRequest(dias=20, tratamiento="ninguno")
    frame = LungSimulationFrame(
        dia=20,
        volumen_sensible=1.0,
        volumen_resistente=0.1,
        volumen_total=1.1,
        fraccion_resistente=0.1,
        progreso=0.2,
        estadio="IA",
    )
    state = teacher_state_from_lung(request, frame)
    assert state.treatment_days == 0
