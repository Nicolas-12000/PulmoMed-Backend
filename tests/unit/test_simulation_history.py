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


# =============================================================================
# Tests Exhaustivos de Branching (tipo Git)
# =============================================================================

class TestSimulationHistoryBranching:
    """Tests avanzados de ramificación tipo Git."""

    def test_multiple_branches_from_same_checkpoint(self):
        """Crear múltiples ramas desde el mismo punto."""
        history = SimulationHistory()

        # Estado inicial
        state_base = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        base_id = history.initialize(state_base, "Estado inicial")

        # Rama 1: Quimioterapia
        history.create_branch("quimio-branch")
        state_quimio = {
            "volumen_tumor_sensible": 8.0,
            "volumen_tumor_resistente": 1.2,
            "tratamiento_activo": "quimio",
            "dias_tratamiento": 30,
        }
        history.save_state(state_quimio, force_snapshot=True)
        quimio_result = history.current_node.snapshot.sensitive_cells

        # Volver al checkpoint base
        history.go_to_checkpoint(base_id)

        # Rama 2: Radioterapia
        history.create_branch("radio-branch")
        state_radio = {
            "volumen_tumor_sensible": 7.0,
            "volumen_tumor_resistente": 1.5,
            "tratamiento_activo": "radio",
            "dias_tratamiento": 30,
        }
        history.save_state(state_radio, force_snapshot=True)
        radio_result = history.current_node.snapshot.sensitive_cells

        # Verificar que ambas ramas existen y son diferentes
        assert quimio_result == 8.0
        assert radio_result == 7.0

        # El nodo raíz debe tener 2 hijos (2 ramas)
        assert len(history.root_node.children) == 2

    def test_deep_branching(self):
        """Crear rama desde una rama existente (branching profundo)."""
        history = SimulationHistory()

        # Estado inicial
        state = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        history.initialize(state)

        # Avanzar en rama main
        for day in [30, 60, 90]:
            state["dias_tratamiento"] = day
            state["volumen_tumor_sensible"] = 10.0 + day * 0.1
            history.save_state(state, force_snapshot=True)

        # Crear sub-rama desde día 90
        history.create_branch("experimental-desde-90")

        state["dias_tratamiento"] = 120
        state["tratamiento_activo"] = "inmuno"
        history.save_state(state, force_snapshot=True)

        # Verificar profundidad
        assert history.current_branch == "experimental-desde-90"
        checkpoints = history.get_checkpoints()
        assert len(checkpoints) >= 4  # inicial + 30 + 60 + 90 + 120

    def test_branch_isolation(self):
        """Cambios en una rama no afectan otra."""
        history = SimulationHistory()

        state = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        base_id = history.initialize(state)

        # Rama A: muchos cambios
        history.create_branch("rama-a")
        for i in range(1, 50):
            state["dias_tratamiento"] = i
            state["volumen_tumor_sensible"] = 10.0 + i
            history.save_state(state)

        # Volver a base
        history.go_to_checkpoint(base_id)

        # Rama B: pocos cambios
        history.create_branch("rama-b")
        state["dias_tratamiento"] = 1
        state["volumen_tumor_sensible"] = 11.0
        history.save_state(state)

        # Al volver a base, el estado debe ser el original
        restored = history.go_to_checkpoint(base_id)
        assert restored["sensitive_cells"] == 10.0
        assert restored["time_point"] == 0


class TestSimulationHistoryOptimization:
    """Tests de optimización de memoria."""

    def test_delta_vs_snapshot_efficiency(self):
        """Deltas usan menos memoria que snapshots equivalentes."""
        history = SimulationHistory(snapshot_interval=100, max_deltas=50)

        state = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        history.initialize(state)

        # Crear 30 deltas (no deben crear snapshots)
        for i in range(1, 31):
            state["dias_tratamiento"] = i
            state["volumen_tumor_sensible"] += 0.1
            history.save_state(state)

        usage = history.get_memory_usage()

        # 1 snapshot + 30 deltas
        assert history.total_snapshots == 1
        assert history.total_deltas == 30

        # Memoria: ~100 bytes snapshot + ~25 bytes * 30 deltas = ~850 bytes
        # vs 31 snapshots = ~3100 bytes (3.6x más)
        expected_max_bytes = 1000  # Debería ser ~850
        assert usage["total_bytes"] < expected_max_bytes

    def test_max_deltas_triggers_snapshot(self):
        """Al superar max_deltas, se crea snapshot automático."""
        history = SimulationHistory(snapshot_interval=1000, max_deltas=10)

        state = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        history.initialize(state)

        # Crear más de max_deltas estados
        for i in range(1, 25):
            state["dias_tratamiento"] = i
            state["volumen_tumor_sensible"] += 0.1
            tipo, _ = history.save_state(state)

            # Después del delta 10, debe crear snapshot
            if i == 11:
                assert tipo == "snapshot"

        # Deben existir varios snapshots por exceder max_deltas
        assert history.total_snapshots > 1

    def test_snapshot_interval_triggers_snapshot(self):
        """Al superar snapshot_interval días, se crea snapshot."""
        history = SimulationHistory(snapshot_interval=30, max_deltas=1000)

        state = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        history.initialize(state)

        # Día 29: debe ser delta
        state["dias_tratamiento"] = 29
        tipo, _ = history.save_state(state)
        assert tipo == "delta"

        # Día 35: debe ser snapshot (supera intervalo de 30)
        state["dias_tratamiento"] = 35
        tipo, _ = history.save_state(state)
        assert tipo == "snapshot"


class TestSimulationHistoryEdgeCases:
    """Tests de casos límite y errores."""

    def test_rewind_at_root(self):
        """Rewind en nodo raíz retorna None."""
        history = SimulationHistory()

        state = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        history.initialize(state)

        result = history.rewind()
        assert result is None

    def test_fast_forward_at_leaf(self):
        """Fast forward en nodo hoja retorna None."""
        history = SimulationHistory()

        state = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        history.initialize(state)

        result = history.fast_forward()
        assert result is None

    def test_go_to_nonexistent_checkpoint(self):
        """Ir a checkpoint inexistente retorna None."""
        history = SimulationHistory()

        state = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        history.initialize(state)

        result = history.go_to_checkpoint("nonexistent-id-12345")
        assert result is None

    def test_save_state_without_initialize(self):
        """Guardar estado sin inicializar crea nodo raíz."""
        history = SimulationHistory()

        state = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }

        tipo, node_id = history.save_state(state)

        assert tipo == "snapshot"
        assert history.total_snapshots == 1
        assert history.root_node is not None

    def test_empty_history_checkpoints(self):
        """Historia vacía retorna lista vacía de checkpoints."""
        history = SimulationHistory()
        checkpoints = history.get_checkpoints()
        assert checkpoints == []

    def test_serialization_roundtrip(self):
        """Serializar y deserializar mantiene datos."""
        history = SimulationHistory()

        state = {
            "volumen_tumor_sensible": 10.0,
            "volumen_tumor_resistente": 1.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        history.initialize(state, "Estado inicial")

        for day in [30, 60, 90]:
            state["dias_tratamiento"] = day
            state["volumen_tumor_sensible"] = 10.0 + day * 0.1
            history.save_state(state, force_snapshot=True)

        # Serializar
        data = history.to_dict()

        # Verificar estructura
        assert "snapshot_interval" in data
        assert "checkpoints" in data
        assert len(data["checkpoints"]) == 4


class TestSimulationHistoryIntegration:
    """Tests de integración con flujos reales."""

    def test_exam_mode_simulation(self):
        """Simula flujo de modo examen (lineal, sin branches)."""
        history = SimulationHistory(snapshot_interval=30, max_deltas=50)

        # Estado inicial del examen
        state = {
            "volumen_tumor_sensible": 15.0,
            "volumen_tumor_resistente": 2.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        history.initialize(state, "Inicio examen")

        # Estudiante aplica tratamientos
        treatments = [
            (10, "quimio"),
            (20, "quimio"),
            (30, "radio"),  # Cambio de tratamiento
            (40, "radio"),
            (50, "ninguno"),  # Pausa
            (60, "inmuno"),
        ]

        for day, treatment in treatments:
            state["dias_tratamiento"] = day
            state["tratamiento_activo"] = treatment
            state["volumen_tumor_sensible"] = 15.0 - day * 0.1
            history.save_state(state)

        stats = history.get_statistics()

        # Verificar estructura lineal
        assert stats["total_snapshots"] >= 1
        assert stats["total_deltas"] + stats["total_snapshots"] >= 6

    def test_free_mode_experimentation(self):
        """Simula flujo de modo libre con experimentación."""
        history = SimulationHistory(snapshot_interval=30, max_deltas=100)

        # Estado inicial
        state = {
            "volumen_tumor_sensible": 20.0,
            "volumen_tumor_resistente": 3.0,
            "tratamiento_activo": "ninguno",
            "dias_tratamiento": 0,
        }
        base_id = history.initialize(state, "Estado base")

        # Experimento 1: Solo quimio (forzar snapshot al final)
        history.create_branch("solo-quimio")
        for day in range(1, 61):
            state["dias_tratamiento"] = day
            state["tratamiento_activo"] = "quimio"
            state["volumen_tumor_sensible"] = 20.0 - day * 0.15
            # Forzar snapshot en día 60
            force = (day == 60)
            history.save_state(state, force_snapshot=force)
        quimio_final = history.current_node.snapshot.sensitive_cells

        # Volver a base para experimento 2
        history.go_to_checkpoint(base_id)

        # Experimento 2: Quimio + Radio (forzar snapshot al final)
        history.create_branch("combo-quimio-radio")
        state = {
            "volumen_tumor_sensible": 20.0,
            "volumen_tumor_resistente": 3.0,
            "tratamiento_activo": "quimio",
            "dias_tratamiento": 0,
        }
        for day in range(1, 31):
            state["dias_tratamiento"] = day
            state["tratamiento_activo"] = "quimio"
            state["volumen_tumor_sensible"] = 20.0 - day * 0.2
            history.save_state(state)

        for day in range(31, 61):
            state["dias_tratamiento"] = day
            state["tratamiento_activo"] = "radio"
            state["volumen_tumor_sensible"] = max(1.0, 14.0 - (day - 30) * 0.3)
            # Forzar snapshot en día 60
            force = (day == 60)
            history.save_state(state, force_snapshot=force)
        combo_final = history.current_node.snapshot.sensitive_cells

        # Comparar resultados
        # Combo debería ser más efectivo (menor volumen)
        assert combo_final <= quimio_final

        # Verificar estructura: al menos 2 checkpoints
        # (base + snapshots forzados de cada rama)
        checkpoints = history.get_checkpoints()
        assert len(checkpoints) >= 2  # base + ramas con snapshots


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
