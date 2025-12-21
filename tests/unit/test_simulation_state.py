from app.models.simulation_state import SimulationState, LungState


def make_state(vol_sensible=0.0, vol_resistant=0.0, edad=30, es_fumador=False, pack_years=0.0):
    return SimulationState(
        edad=edad,
        es_fumador=es_fumador,
        pack_years=pack_years,
        dias_desde_cambio_tabaco=0,
        lung_state=None,
        dieta="normal",
        volumen_tumor_sensible=vol_sensible,
        volumen_tumor_resistente=vol_resistant,
        tratamiento_activo="ninguno",
        dias_tratamiento=0,
    )


def test_volumen_total_and_risk_and_state():
    s = make_state(vol_sensible=0.5, vol_resistant=0.0, edad=40)
    assert s.volumen_total == 0.5
    score = s.compute_risk_score()
    assert 0.0 <= score <= 1.0

    state = s.update_lung_state()
    # Small volume -> ESTABLE expected
    assert state in (LungState.ESTABLE, LungState.EN_RIESGO)


def test_smoking_accumulation_and_stop():
    s = make_state(vol_sensible=0.0, edad=50, es_fumador=True, pack_years=0.0)
    s.start_smoking()
    assert s.es_fumador is True
    s.advance_time_and_accumulate_smoking(days=365, cigarettes_per_day=20)
    # One year of 20 cigs/day => ~1 pack-year
    assert s.pack_years >= 0.9 and s.pack_years <= 1.1

    s.stop_smoking()
    assert s.es_fumador is False
    # advancing with non-positive days does nothing
    prev = s.pack_years
    s.advance_time_and_accumulate_smoking(days=0)
    assert s.pack_years == prev


def test_estadio_aproximado_thresholds():
    s = make_state(vol_sensible=2.0)
    assert s.estadio_aproximado.startswith("IA")

    s = make_state(vol_sensible=10.0)
    assert s.estadio_aproximado.startswith("IB") or s.estadio_aproximado.startswith("IIA")

    s = make_state(vol_sensible=30.0)
    assert s.estadio_aproximado.startswith("IIB") or s.estadio_aproximado.startswith("IIIA")
