"""
app/services/simulation_history_service.py
Servicio de historial de simulaciones para el modo libre

Características:
- Snapshots cada N pasos (configurable)
- Deltas incrementales entre snapshots
- Branch/rewind para experimentar tratamientos
- Persistencia en base de datos (opcional)
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple


class SimulationSnapshot:
    """Snapshot completo del estado de simulación"""

    def __init__(
        self,
        time_point: float,
        sensitive_cells: float,
        resistant_cells: float,
        treatment_type: str,
        description: str = "",
    ):
        self.time_point = time_point
        self.sensitive_cells = sensitive_cells
        self.resistant_cells = resistant_cells
        self.treatment_type = treatment_type
        self.description = description
        self.timestamp = datetime.now()

    @property
    def total_volume(self) -> float:
        return self.sensitive_cells + self.resistant_cells

    def to_dict(self) -> dict:
        return {
            "time_point": self.time_point,
            "sensitive_cells": self.sensitive_cells,
            "resistant_cells": self.resistant_cells,
            "treatment_type": self.treatment_type,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "total_volume": self.total_volume,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SimulationSnapshot":
        snapshot = cls(
            time_point=data["time_point"],
            sensitive_cells=data["sensitive_cells"],
            resistant_cells=data["resistant_cells"],
            treatment_type=data["treatment_type"],
            description=data.get("description", ""),
        )
        if "timestamp" in data:
            snapshot.timestamp = datetime.fromisoformat(data["timestamp"])
        return snapshot

    def __repr__(self):
        return f"Snapshot(t={self.time_point:.1f}, V={self.total_volume:.2f} cm³)"


class SimulationDelta:
    """Delta incremental entre snapshots (solo cambios)"""

    def __init__(
        self,
        delta_time: float,
        delta_sensitive: float,
        delta_resistant: float,
        treatment_changed: bool = False,
        new_treatment: Optional[str] = None,
    ):
        self.delta_time = delta_time
        self.delta_sensitive = delta_sensitive
        self.delta_resistant = delta_resistant
        self.treatment_changed = treatment_changed
        self.new_treatment = new_treatment

    def apply_forward(self, base_snapshot: SimulationSnapshot) -> SimulationSnapshot:
        """Aplica delta hacia adelante"""
        return SimulationSnapshot(
            time_point=base_snapshot.time_point + self.delta_time,
            sensitive_cells=base_snapshot.sensitive_cells + self.delta_sensitive,
            resistant_cells=base_snapshot.resistant_cells + self.delta_resistant,
            treatment_type=(
                self.new_treatment
                if self.treatment_changed
                else base_snapshot.treatment_type
            ),
            description="Delta applied",
        )

    def apply_backward(
        self, current_snapshot: SimulationSnapshot, prev_treatment: str
    ) -> SimulationSnapshot:
        """Revierte delta hacia atrás"""
        return SimulationSnapshot(
            time_point=current_snapshot.time_point - self.delta_time,
            sensitive_cells=current_snapshot.sensitive_cells - self.delta_sensitive,
            resistant_cells=current_snapshot.resistant_cells - self.delta_resistant,
            treatment_type=(
                prev_treatment
                if self.treatment_changed
                else current_snapshot.treatment_type
            ),
            description="Delta reverted",
        )

    @staticmethod
    def from_snapshots(
        from_snap: SimulationSnapshot, to_snap: SimulationSnapshot
    ) -> "SimulationDelta":
        """Crea delta entre dos snapshots"""
        return SimulationDelta(
            delta_time=to_snap.time_point - from_snap.time_point,
            delta_sensitive=to_snap.sensitive_cells - from_snap.sensitive_cells,
            delta_resistant=to_snap.resistant_cells - from_snap.resistant_cells,
            treatment_changed=to_snap.treatment_type != from_snap.treatment_type,
            new_treatment=(
                to_snap.treatment_type
                if to_snap.treatment_type != from_snap.treatment_type
                else None
            ),
        )

    def to_dict(self) -> dict:
        return {
            "delta_time": self.delta_time,
            "delta_sensitive": self.delta_sensitive,
            "delta_resistant": self.delta_resistant,
            "treatment_changed": self.treatment_changed,
            "new_treatment": self.new_treatment,
        }

    def get_size_bytes(self) -> int:
        """Tamaño aproximado en bytes (muy pequeño)"""
        return 3 * 4 + 1 + 8  # 3 floats + 1 bool + 1 string ref


class HistoryNode:
    """Nodo en el árbol de historial (permite branching)"""

    def __init__(self, snapshot: SimulationSnapshot):
        self.id = datetime.now().strftime("%Y%m%d%H%M%S%f")[:16]
        self.snapshot = snapshot
        self.deltas_to_next: List[SimulationDelta] = []
        self.parent: Optional["HistoryNode"] = None
        self.children: List["HistoryNode"] = []
        self.is_checkpoint = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "snapshot": self.snapshot.to_dict(),
            "is_checkpoint": self.is_checkpoint,
            "children_count": len(self.children),
            "deltas_count": len(self.deltas_to_next),
        }


class SimulationHistory:
    """
    Sistema completo de historial tipo Git para simulaciones

    Optimización: Snapshots completos + Deltas incrementales
    """

    def __init__(self, snapshot_interval: int = 100, max_deltas: int = 100):
        """
        Args:
            snapshot_interval: Crear snapshot cada N pasos (default: 100)
            max_deltas: Máximo de deltas entre snapshots (default: 100)
        """
        self.snapshot_interval = snapshot_interval
        self.max_deltas = max_deltas
        self.root_node: Optional[HistoryNode] = None
        self.current_node: Optional[HistoryNode] = None
        self.current_branch = "main"

        self.total_snapshots = 0
        self.total_deltas = 0

    def initialize(
        self, simulation_state: dict, description: str = "Initial state"
    ) -> str:
        """
        Inicializa historial con estado inicial

        Returns:
            ID del nodo raíz
        """
        snapshot = SimulationSnapshot(
            time_point=simulation_state.get("dias_tratamiento", 0),
            sensitive_cells=simulation_state["volumen_tumor_sensible"],
            resistant_cells=simulation_state["volumen_tumor_resistente"],
            treatment_type=simulation_state.get("tratamiento_activo", "ninguno"),
            description=description,
        )

        self.root_node = HistoryNode(snapshot)
        self.current_node = self.root_node
        self.total_snapshots = 1

        return self.root_node.id

    def save_state(
        self, simulation_state: dict, force_snapshot: bool = False
    ) -> Tuple[str, str]:
        """
        Guarda estado actual (crea delta o snapshot según configuración)

        Returns:
            (tipo, id) - tipo es "snapshot" o "delta", id es el identificador
        """
        if self.current_node is None:
            node_id = self.initialize(simulation_state, "Auto-initialized")
            return ("snapshot", node_id)

        new_snapshot = SimulationSnapshot(
            time_point=simulation_state.get("dias_tratamiento", 0),
            sensitive_cells=simulation_state["volumen_tumor_sensible"],
            resistant_cells=simulation_state["volumen_tumor_resistente"],
            treatment_type=simulation_state.get("tratamiento_activo", "ninguno"),
        )

        # Decidir si crear snapshot o delta
        should_create_snapshot = (
            force_snapshot
            or len(self.current_node.deltas_to_next) >= self.max_deltas
            or (new_snapshot.time_point - self.current_node.snapshot.time_point)
            >= self.snapshot_interval
        )

        if should_create_snapshot:
            # Crear nuevo nodo checkpoint
            new_node = HistoryNode(new_snapshot)
            new_node.parent = self.current_node
            self.current_node.children.append(new_node)
            self.current_node = new_node
            self.total_snapshots += 1

            return ("snapshot", new_node.id)
        else:
            # Crear delta incremental
            delta = SimulationDelta.from_snapshots(
                self.current_node.snapshot, new_snapshot
            )
            self.current_node.deltas_to_next.append(delta)
            self.total_deltas += 1

            return ("delta", f"delta_{self.total_deltas}")

    def rewind(self, steps: int = 1) -> Optional[dict]:
        """
        Retrocede N pasos en el historial

        Returns:
            Estado restaurado o None si no es posible
        """
        if self.current_node is None or self.current_node.parent is None:
            return None

        # Simplificado: ir al snapshot anterior
        self.current_node = self.current_node.parent
        return self.current_node.snapshot.to_dict()

    def fast_forward(self, steps: int = 1) -> Optional[dict]:
        """
        Avanza N pasos en el historial (si existe)

        Returns:
            Estado avanzado o None si no hay más adelante
        """
        if self.current_node is None or len(self.current_node.children) == 0:
            return None

        # Avanzar al primer hijo
        self.current_node = self.current_node.children[0]
        return self.current_node.snapshot.to_dict()

    def create_branch(self, branch_name: str) -> str:
        """
        Crea una rama (branch) para experimentar

        Returns:
            ID del checkpoint actual
        """
        self.current_branch = branch_name
        return self.current_node.id if self.current_node else None

    def go_to_checkpoint(self, checkpoint_id: str) -> Optional[dict]:
        """
        Vuelve a un checkpoint específico por ID

        Returns:
            Estado del checkpoint o None si no existe
        """
        node = self._find_node_by_id(self.root_node, checkpoint_id)
        if node:
            self.current_node = node
            return node.snapshot.to_dict()
        return None

    def get_checkpoints(self) -> List[Dict]:
        """
        Obtiene lista de checkpoints disponibles

        Returns:
            Lista de dicts con id, time, description
        """
        checkpoints = []
        self._collect_checkpoints(self.root_node, checkpoints)
        return checkpoints

    def get_memory_usage(self) -> Dict[str, any]:
        """
        Calcula uso de memoria del historial

        Returns:
            Dict con estadísticas de memoria
        """
        total_bytes = 0
        self._count_memory_usage(self.root_node, total_bytes)

        # Aproximación: cada snapshot ~100 bytes, cada delta ~25 bytes
        snapshot_bytes = self.total_snapshots * 100
        delta_bytes = self.total_deltas * 25
        total_bytes = snapshot_bytes + delta_bytes

        return {
            "snapshots": self.total_snapshots,
            "deltas": self.total_deltas,
            "total_bytes": total_bytes,
            "total_kb": total_bytes / 1024,
            "total_mb": total_bytes / (1024 * 1024),
        }

    def get_statistics(self) -> Dict[str, any]:
        """Obtiene estadísticas completas del historial"""
        return {
            "total_snapshots": self.total_snapshots,
            "total_deltas": self.total_deltas,
            "current_branch": self.current_branch,
            "current_node_id": self.current_node.id if self.current_node else None,
            "memory_usage": self.get_memory_usage(),
            "checkpoints_count": len(self.get_checkpoints()),
        }

    def to_dict(self) -> dict:
        """Serializa el historial completo"""
        return {
            "snapshot_interval": self.snapshot_interval,
            "max_deltas": self.max_deltas,
            "current_branch": self.current_branch,
            "statistics": self.get_statistics(),
            "checkpoints": self.get_checkpoints(),
        }

    # === Métodos auxiliares privados ===

    def _find_node_by_id(
        self, node: HistoryNode, node_id: str
    ) -> Optional[HistoryNode]:
        """Busca nodo recursivamente por ID"""
        if node is None:
            return None
        if node.id == node_id:
            return node

        for child in node.children:
            result = self._find_node_by_id(child, node_id)
            if result:
                return result

        return None

    def _collect_checkpoints(self, node: HistoryNode, checkpoints: List):
        """Recolecta checkpoints recursivamente"""
        if node is None:
            return

        if node.is_checkpoint:
            checkpoints.append(
                {
                    "id": node.id,
                    "time": node.snapshot.time_point,
                    "description": node.snapshot.description,
                    "total_volume": node.snapshot.total_volume,
                    "treatment": node.snapshot.treatment_type,
                }
            )

        for child in node.children:
            self._collect_checkpoints(child, checkpoints)

    def _count_memory_usage(self, node: HistoryNode, total_bytes: int):
        """Cuenta uso de memoria recursivamente"""
        if node is None:
            return

        # Contar memoria de este nodo
        for child in node.children:
            self._count_memory_usage(child, total_bytes)
