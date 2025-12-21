"""
tests/unit/test_simulation_history.py
Tests del sistema de historial tipo Git
"""

import pytest

from app.services.simulation_history_service import (
    SimulationDelta,
    SimulationHistory,
    SimulationSnapshot,
)


class TestSimulationSnapshot:
    """Tests de snapshots"""

    def test_snapshot_creation(self):
        snapshot = SimulationSnapshot(
            time_point=30.0,
            sensitive_cells=50.0,
            resistant_cells=10.0,
            treatment_type="quimio",
            description="Test snapshot",
        )

        assert snapshot.time_point == 30.0
        assert snapshot.sensitive_cells == 50.0
        assert snapshot.resistant_cells == 10.0
        assert snapshot.total_volume == 60.0
        assert snapshot.treatment_type == "quimio"

    def test_snapshot_serialization(self):
        snapshot = SimulationSnapshot(
            time_point=15.0,
            sensitive_cells=20.0,
            resistant_cells=5.0,
            treatment_type="ninguno",
        )

        data = snapshot.to_dict()

        assert "time_point" in data
        assert "sensitive_cells" in data
        assert data["total_volume"] == 25.0

        # Deserializar
        restored = SimulationSnapshot.from_dict(data)
        assert restored.time_point == snapshot.time_point
        assert restored.sensitive_cells == snapshot.sensitive_cells


class TestSimulationDelta:
    """Tests de deltas incrementales"""

    def test_delta_creation(self):
        snap1 = SimulationSnapshot(0, 10.0, 1.0, "ninguno")
        snap2 = SimulationSnapshot(5, 12.0, 1.2, "ninguno")

        delta = SimulationDelta.from_snapshots(snap1, snap2)

        assert delta.delta_time == 5.0
        assert delta.delta_sensitive == 2.0
        assert abs(delta.delta_resistant - 0.2) < 0.001  # Floating point precision
        assert not delta.treatment_changed

    def test_delta_with_treatment_change(self):
        snap1 = SimulationSnapshot(0, 10.0, 1.0, "ninguno")
        snap2 = SimulationSnapshot(5, 9.0, 1.1, "quimio")

        delta = SimulationDelta.from_snapshots(snap1, snap2)

        assert delta.treatment_changed
        assert delta.new_treatment == "quimio"

    def test_delta_apply_forward(self):
        base = SimulationSnapshot(0, 10.0, 1.0, "ninguno")
        delta = SimulationDelta(
            delta_time=5.0,
            delta_sensitive=2.0,
            delta_resistant=0.5,
            treatment_changed=False,
        )

        result = delta.apply_forward(base)

        assert result.time_point == 5.0
        assert result.sensitive_cells == 12.0
        assert result.resistant_cells == 1.5
        assert result.treatment_type == "ninguno"

    def test_delta_apply_backward(self):
        current = SimulationSnapshot(5, 12.0, 1.5, "ninguno")
        delta = SimulationDelta(
            delta_time=5.0,
            delta_sensitive=2.0,
            delta_resistant=0.5,
            treatment_changed=False,
        )

        result = delta.apply_backward(current, "ninguno")

        assert result.time_point == 0.0
        assert result.sensitive_cells == 10.0
        assert result.resistant_cells == 1.0


class TestSimulationHistory:
    """Tests del sistema completo de historial"""

    def test_history_initialization(self):
        history = SimulationHistory(snapshot_interval=50, max_deltas=50)

        state = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }

        node_id = history.initialize(state, "Initial state")

        assert history.total_snapshots == 1
        assert history.total_deltas == 0
        assert node_id is not None

    def test_save_state_creates_deltas(self):
        history = SimulationHistory(snapshot_interval=100, max_deltas=100)

        # Inicializar
        state1 = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        history.initialize(state1)

        # Guardar estados cercanos (deben crear deltas)
        for day in range(1, 10):
            state = {
                "volumen_tumor_sensible": 10.0 + day * 0.5,
                "volumen_tumor_resistente": 1.0 + day * 0.1,
                "tratamiento_activo": "ninguno",
                "dias_tratamiento": day,
            }
            tipo, _ = history.save_state(state)

            assert tipo == "delta", f"Día {day} debería crear delta"

        assert history.total_deltas == 9
        assert history.total_snapshots == 1  # Solo el inicial

    def test_save_state_creates_snapshot_after_interval(self):
        history = SimulationHistory(snapshot_interval=50, max_deltas=100)

        # Inicializar
        state1 = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        history.initialize(state1)

        # Saltar 60 días (excede snapshot_interval=50)
        state2 = {
            "volumen_tumor_sensible": 15.0,
            "volumen_tumor_resistente": 2.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 60,
        }
        tipo, _ = history.save_state(state2)

        assert tipo == "snapshot", "Después de 60 días debe crear snapshot"
        assert history.total_snapshots == 2

    def test_force_snapshot(self):
        history = SimulationHistory(snapshot_interval=100, max_deltas=100)

        state1 = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        history.initialize(state1)

        state2 = {
            "volumen_tumor_sensible": 11.0,
            "volumen_tumor_resistente": 1.1,
            "tratamiento_activo": "quimio",
            "dias_tratamiento": 5,
        }
        tipo, _ = history.save_state(state2, force_snapshot=True)

        assert tipo == "snapshot", "force_snapshot debe crear snapshot"
        assert history.total_snapshots == 2

    def test_rewind(self):
        history = SimulationHistory()

        state1 = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        history.initialize(state1)

        state2 = {
            "volumen_tumor_sensible": 15.0,
            "volumen_tumor_resistente": 2.0,
            "tratamiento_activo": "quimio",
            "dias_tratamiento": 60,
        }
        history.save_state(state2, force_snapshot=True)

        # Retroceder
        restored = history.rewind()

        assert restored is not None
        assert restored["sensitive_cells"] == 10.0
        assert restored["time_point"] == 0

    def test_fast_forward(self):
        history = SimulationHistory()

        state1 = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        history.initialize(state1)

        state2 = {
            "volumen_tumor_sensible": 15.0,
            "volumen_tumor_resistente": 2.0,
            "tratamiento_activo": "quimio",
            "dias_tratamiento": 60,
        }
        history.save_state(state2, force_snapshot=True)

        # Retroceder
        history.rewind()

        # Avanzar de nuevo
        advanced = history.fast_forward()

        assert advanced is not None
        assert advanced["sensitive_cells"] == 15.0
        assert advanced["time_point"] == 60

    def test_create_branch(self):
        history = SimulationHistory()

        state = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        history.initialize(state)

        checkpoint_id = history.create_branch("tratamiento-experimental")

        assert history.current_branch == "tratamiento-experimental"
        assert checkpoint_id is not None

    def test_go_to_checkpoint(self):
        history = SimulationHistory()

        state1 = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        checkpoint_id = history.initialize(state1)

        # Avanzar
        state2 = {
            "volumen_tumor_sensible": 15.0,
            "volumen_tumor_resistente": 2.0,
            "tratamiento_activo": "quimio",
            "dias_tratamiento": 60,
        }
        history.save_state(state2, force_snapshot=True)

        # Volver al checkpoint inicial por ID
        restored = history.go_to_checkpoint(checkpoint_id)

        assert restored is not None
        assert restored["sensitive_cells"] == 10.0

    def test_get_checkpoints(self):
        history = SimulationHistory()

        state1 = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        history.initialize(state1, "Estado inicial")

        state2 = {
            "volumen_tumor_sensible": 15.0,
            "volumen_tumor_resistente": 2.0,
            "tratamiento_activo": "quimio",
            "dias_tratamiento": 60,
        }
        history.save_state(state2, force_snapshot=True)

        checkpoints = history.get_checkpoints()

        assert len(checkpoints) == 2
        assert checkpoints[0]["description"] == "Estado inicial"
        assert checkpoints[0]["time"] == 0

    def test_memory_usage(self):
        history = SimulationHistory()

        state = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        history.initialize(state)

        # Crear varios deltas
        for i in range(1, 20):
            state["dias_tratamiento"] = i
            state["volumen_tumor_sensible"] += 0.5
            history.save_state(state)

        usage = history.get_memory_usage()

        assert "snapshots" in usage
        assert "deltas" in usage
        assert "total_bytes" in usage
        assert usage["total_bytes"] > 0

    def test_statistics(self):
        history = SimulationHistory()

        state = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        history.initialize(state)

        stats = history.get_statistics()

        assert "total_snapshots" in stats
        assert "total_deltas" in stats
        assert "current_branch" in stats
        assert "memory_usage" in stats
        assert stats["current_branch"] == "main"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
