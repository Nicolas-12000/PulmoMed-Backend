from app.models.simulation_state import SimulationState, LungState


def make_state(vol_sensible=0.0, vol_resistant=0.0, age=30, is_smoker=False, pack_years=0.0):
    return SimulationState(
        age=age,
        is_smoker=is_smoker,
        pack_years=pack_years,
        days_since_smoking_change=0,
        lung_state=None,
        diet="normal",
        sensitive_tumor_volume=vol_sensible,
        resistant_tumor_volume=vol_resistant,
        active_treatment="ninguno",
        treatment_days=0,
    )


def test_volumen_total_and_risk_and_state():
    s = make_state(vol_sensible=0.5, vol_resistant=0.0, age=40)
    assert s.total_volume == 0.5
    score = s.compute_risk_score()
    assert 0.0 <= score <= 1.0

    state = s.update_lung_state()
    # Small volume -> ESTABLE expected
    assert state in (LungState.ESTABLE, LungState.EN_RIESGO)


def test_smoking_accumulation_and_stop():
    s = make_state(vol_sensible=0.0, age=50, is_smoker=True, pack_years=0.0)
    s.start_smoking()
    assert s.is_smoker is True
    s.advance_time_and_accumulate_smoking(days=365, cigarettes_per_day=20)
    # One year of 20 cigs/day => ~1 pack-year
    assert s.pack_years >= 0.9 and s.pack_years <= 1.1

    s.stop_smoking()
    assert s.is_smoker is False
    # advancing with non-positive days does nothing
    prev = s.pack_years
    s.advance_time_and_accumulate_smoking(days=0)
    assert s.pack_years == prev


def test_estadio_aproximado_thresholds():
    s = make_state(vol_sensible=2.0)
    assert s.approx_stage.startswith("IA")

    s = make_state(vol_sensible=10.0)
    assert s.approx_stage.startswith("IB") or s.approx_stage.startswith("IIA")

    s = make_state(vol_sensible=30.0)
    assert s.approx_stage.startswith("IIB") or s.approx_stage.startswith("IIIA")
