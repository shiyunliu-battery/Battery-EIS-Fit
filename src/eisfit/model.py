from __future__ import annotations

import numpy as np

from .config import TailModel


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
