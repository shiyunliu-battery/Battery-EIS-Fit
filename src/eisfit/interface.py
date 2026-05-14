from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np

from .config import FitConfig, TailModel
from .fitting import FitResult, fit_model_eis
from .io import load_eis
from .pipeline import save_fit_outputs


def fit(
    freq: np.ndarray,
    Zexp: np.ndarray,
    tail: TailModel = "cpe",
    n_starts: int = 40,
    seed: int = 7,
    max_nfev: int = 8000,
    weight: str = "modulus",
    loss: str = "soft_l1",
) -> FitResult:
    cfg = FitConfig(
        tail=tail,
        n_starts=n_starts,
        seed=seed,
        max_nfev=max_nfev,
        weight_func=weight,
        loss=loss,
    )
    return fit_model_eis(freq, Zexp, cfg=cfg)


def fit_file(
    path: str | Path,
    tail: TailModel = "cpe",
    n_starts: int = 40,
    seed: int = 7,
    max_nfev: int = 8000,
    weight: str = "modulus",
    loss: str = "soft_l1",
    out_dir: Optional[str | Path] = None,
) -> FitResult:
    freq, Zexp = load_eis(path)
    result = fit(freq, Zexp, tail=tail, n_starts=n_starts, seed=seed, max_nfev=max_nfev, weight=weight, loss=loss)
    if out_dir is not None:
        save_fit_outputs(path, freq, Zexp, result, out_dir=out_dir)
    return result
