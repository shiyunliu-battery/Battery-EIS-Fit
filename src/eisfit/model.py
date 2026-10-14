from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from .config import TailModel, parameter_names


def z_cpe(Q: float, n: float, w: np.ndarray) -> np.ndarray:
    return 1.0 / (Q * (1j * w) ** n)


def z_warburg(sigma: float, w: np.ndarray) -> np.ndarray:
    return sigma / np.sqrt(1j * w)


def z_parallel(R: float, Zx: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 / R + 1.0 / Zx)


def model_eis(p: np.ndarray, w: np.ndarray, tail: TailModel = "cpe") -> np.ndarray:
    L, R0, R1, Q1, n1, R2, Q2, n2 = p[:8]
    Z = 1j * w * L + R0
    Z += z_parallel(R1, z_cpe(Q1, n1, w))
    Z += z_parallel(R2, z_cpe(Q2, n2, w))
    if tail == "cpe":
        Qd, nd = p[8:10]
        Z += z_cpe(Qd, nd, w)
    elif tail == "warburg":
        (sigma,) = p[8:9]
        Z += z_warburg(sigma, w)
    else:
        raise ValueError(f"Unsupported tail model: {tail}")
    return Z


def model_impedance(parameters: Mapping[str, float], frequency_hz: np.ndarray, tail: TailModel = "cpe") -> np.ndarray:
    """Evaluate the circuit from named parameters, such as ``FitResult.parameters``, at frequencies in Hz."""
    names = parameter_names(tail)
    missing = [name for name in names if name not in parameters]
    unexpected = sorted(set(parameters) - set(names))
    if missing or unexpected:
        raise ValueError(f"Parameters do not match the {tail} model: missing {missing}, unexpected {unexpected}.")
    p = np.array([parameters[name] for name in names], dtype=float)
    return model_eis(p, 2 * np.pi * np.asarray(frequency_hz, dtype=float), tail=tail)


def model_eis_step(p: np.ndarray, w: np.ndarray, step: int, tail: TailModel = "cpe") -> np.ndarray:
    L, R0, R1, Q1, n1, R2, Q2, n2 = p[:8]
    Z = 1j * w * L + R0
    if step >= 2:
        Z += z_parallel(R1, z_cpe(Q1, n1, w))
    if step >= 3:
        Z += z_parallel(R2, z_cpe(Q2, n2, w))
    if step >= 4:
        if tail == "cpe":
            Qd, nd = p[8:10]
            Z += z_cpe(Qd, nd, w)
        elif tail == "warburg":
            (sigma,) = p[8:9]
            Z += z_warburg(sigma, w)
        else:
            raise ValueError(f"Unsupported tail model: {tail}")
    return Z


def rmse_complex(Zsim: np.ndarray, Zexp: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.abs(Zsim - Zexp) ** 2)))
