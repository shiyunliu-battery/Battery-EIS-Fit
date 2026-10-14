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
    # Accepted starts whose cost is within this relative tolerance of the best are reported
    # as near-best in the diagnostics; it does not change which start is selected.
    near_best_rtol: float = 0.01


@dataclass(frozen=True)
class PlotConfig:
    """Figure options for saved fit outputs; they never affect fitting."""

    dpi: int = 300
    close: bool = True


PARAMETER_NAMES_CPE = ["L_H", "R0_Ohm", "R1_Ohm", "Q1", "n1", "R2_Ohm", "Q2", "n2", "Qd", "nd"]
PARAMETER_NAMES_WARBURG = ["L_H", "R0_Ohm", "R1_Ohm", "Q1", "n1", "R2_Ohm", "Q2", "n2", "sigma"]
PARAMETER_NAMES = PARAMETER_NAMES_CPE

# A CPE coefficient Q has unit S*s^n, where n is the exponent of the same element.
PARAMETER_UNITS = {
    "L_H": "H",
    "R0_Ohm": "Ohm",
    "R1_Ohm": "Ohm",
    "R2_Ohm": "Ohm",
    "Q1": "S*s^n",
    "Q2": "S*s^n",
    "Qd": "S*s^n",
    "n1": "1",
    "n2": "1",
    "nd": "1",
    "sigma": "Ohm*s^(-1/2)",
}


def parameter_names(tail: TailModel = "cpe") -> list[str]:
    if tail == "cpe":
        return PARAMETER_NAMES_CPE
    if tail == "warburg":
        return PARAMETER_NAMES_WARBURG
    raise ValueError(f"Unsupported tail model: {tail}")


def parameter_units(tail: TailModel = "cpe") -> dict[str, str]:
    """Return the unit of every parameter of the selected tail model, in reported order."""
    return {name: PARAMETER_UNITS[name] for name in parameter_names(tail)}
