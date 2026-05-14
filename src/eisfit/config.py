from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Tuple

TailModel = Literal["cpe", "warburg"]


@dataclass(frozen=True)
class FitConfig:
    n_starts: int = 40
    seed: int = 7
    max_nfev: int = 8000
    tail: TailModel = "cpe"
    weight_func: str = "modulus"
    weight_eps: float = 1e-9
    loss: str = "soft_l1"
    f_scale: Optional[float] = None
    use_adaptive_bounds: bool = True
    lb: Tuple[float, ...] = (1e-11, 1e-6, 1e-7, 1e-10, 0.3, 1e-7, 1e-10, 0.3, 1e-10, 0.3)
    ub: Tuple[float, ...] = (1e-3, 50.0, 200.0, 1e6, 1.0, 2000.0, 1e6, 1.0, 1e8, 1.0)
    save_png_dpi: int = 300
    show_plot: bool = False
    close_plot: bool = True


PARAMETER_NAMES_CPE = ["L_H", "R0_Ohm", "R1_Ohm", "Q1", "n1", "R2_Ohm", "Q2", "n2", "Qd", "nd"]
PARAMETER_NAMES_WARBURG = ["L_H", "R0_Ohm", "R1_Ohm", "Q1", "n1", "R2_Ohm", "Q2", "n2", "sigma"]
PARAMETER_NAMES = PARAMETER_NAMES_CPE


def parameter_names(tail: TailModel = "cpe") -> list[str]:
    if tail == "cpe":
        return PARAMETER_NAMES_CPE
    if tail == "warburg":
        return PARAMETER_NAMES_WARBURG
    raise ValueError(f"Unsupported tail model: {tail}")
