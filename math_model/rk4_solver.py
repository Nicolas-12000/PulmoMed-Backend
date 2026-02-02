"""
RK4Solver - Integrador numérico Runge-Kutta de 4to orden
"""
from typing import Callable, List
import numpy as np


class RK4Solver:
    """
    Solver Runge-Kutta de 4to orden para sistemas de ODEs

    Usado para resolver las ecuaciones diferenciales de Gompertz:
        dNs/dt = rs * Ns * ln(K/(Ns+Nr)) - β(t) * Ns
        dNr/dt = rr * Nr * ln(K/(Ns+Nr))

    RK4 es preciso, estable y eficiente para este tipo de sistemas
    Precisión O(h^4), robusto para sistemas stiff moderados
    """

    def __init__(
        self,
        derivative_func: Callable[[float, np.ndarray], np.ndarray],
        step_size: float = 0.1
    ):
        """
        Constructor del solver

        Args:
            derivative_func: Función que calcula derivadas f(t, y) -> dy/dt
            step_size: Paso de integración (días). Default: 0.1
        """
        if derivative_func is None:
            raise ValueError("derivative_func no puede ser None")

        if step_size <= 0 or step_size > 1.0:
            raise ValueError(f"Step size debe estar en (0, 1.0] días, got {step_size}")

        self.derivative_func = derivative_func
        self.step_size = step_size

    def step(self, t: float, y: np.ndarray) -> np.ndarray:
        """
        Realiza un paso de integración RK4

        Args:
            t: Tiempo actual
            y: Estado actual [Ns, Nr]

        Returns:
            Nuevo estado [Ns', Nr']
        """
        if len(y) != 2:
            raise ValueError(f"Estado debe ser array de 2 elementos, got {len(y)}")

        h = self.step_size

        # Cálculo de pendientes RK4
        k1 = self.derivative_func(t, y)
        k2 = self.derivative_func(t + 0.5 * h, y + 0.5 * h * k1)
        k3 = self.derivative_func(t + 0.5 * h, y + 0.5 * h * k2)
        k4 = self.derivative_func(t + h, y + h * k3)

        # Combinación ponderada (1/6, 1/3, 1/3, 1/6)
        y_next = y + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

        # Protección contra valores negativos (no físicos)
        y_next = np.maximum(y_next, 0.0)

        return y_next

    def integrate(
        self,
        t0: float,
        y0: np.ndarray,
        t_final: float,
        record_history: bool = False
    ) -> tuple[np.ndarray, List[tuple[float, np.ndarray]]]:
        """
        Integra el sistema desde t0 hasta t_final

        Args:
            t0: Tiempo inicial
            y0: Estado inicial [Ns0, Nr0]
            t_final: Tiempo final
            record_history: Si True, guarda todos los pasos intermedios

        Returns:
            Tupla (estado_final, historial)
            - estado_final: [Ns(t_final), Nr(t_final)]
            - historial: Lista de (t, [Ns, Nr]) si record_history=True
        """
        if t_final < t0:
            raise ValueError(f"t_final ({t_final}) debe ser >= t0 ({t0})")

        y = np.array(y0, dtype=float)
        t = t0
        history = [(t, y.copy())] if record_history else []

        while t < t_final:
            # Ajustar último paso si excede t_final
            h = min(self.step_size, t_final - t)
            if h < 0.001:  # Evitar pasos infinitesimales
                break

            # Paso RK4
            y = self.step(t, y)
            t += self.step_size

            if record_history:
                history.append((t, y.copy()))

        return y, history

    def integrate_days(
        self,
        y0: np.ndarray,
        days: int,
        record_daily: bool = True
    ) -> List[tuple[int, np.ndarray]]:
        """
        Integra el sistema por N días, retornando estado diario

        Args:
            y0: Estado inicial [Ns0, Nr0]
            days: Número de días a simular
            record_daily: Si True, guarda estado al final de cada día

        Returns:
            Lista de (día, [Ns, Nr])
        """
        y = np.array(y0, dtype=float)
        t = 0.0
        daily_states = [(0, y.copy())]

        for day in range(1, days + 1):
            y, _ = self.integrate(t, y, t + 1.0, record_history=False)
            t += 1.0

            if record_daily:
                daily_states.append((day, y.copy()))

        return daily_states
