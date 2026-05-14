"""Compatibility wrapper for the packaged EIS fitting pipeline.

New code should import from ``eisfit`` directly. This module is kept so older
notebooks/scripts using ``import eis_pipeline`` continue to work.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from eisfit import (
    FitConfig,
    fit,
    fit_file,
    fit_model_eis,
    load_eis,
    model_eis,
    model_eis_step,
    parameter_names,
    process_file,
    process_folder,
    rmse_complex,
    save_fit_outputs,
    z_warburg,
)
from eisfit.fitting import get_bound_hits as report_bound_hits
from eisfit.fitting import initial_guess as _initial_guess
from eisfit.fitting import make_bounds_from_data, random_in_bounds as _random_in_bounds
from eisfit.io import find_column as _find_col
from eisfit.model import z_cpe as Z_cpe
from eisfit.model import z_parallel as Z_par
from eisfit.model import z_warburg as Z_warburg


def load_eis_from_excel(path: str | Path, sheet_name: Optional[str] = None):
    return load_eis(path, sheet_name=sheet_name)


def process_one_file(path: str | Path, sheet_name: Optional[str] = None, cfg: FitConfig = FitConfig(), out_dir: Optional[str | Path] = None):
    return process_file(path, cfg=cfg, out_dir=out_dir, sheet_name=sheet_name)


def save_outputs(input_path, freq, Zexp, fit, out_dir=None, cfg: FitConfig = FitConfig()):
    target_dir = out_dir if out_dir is not None else Path(input_path).resolve().parent
    return save_fit_outputs(input_path, freq, Zexp, fit, out_dir=target_dir, cfg=cfg)


__all__ = [
    "FitConfig",
    "Z_cpe",
    "Z_par",
    "Z_warburg",
    "fit",
    "fit_file",
    "fit_model_eis",
    "load_eis",
    "load_eis_from_excel",
    "make_bounds_from_data",
    "model_eis",
    "model_eis_step",
    "parameter_names",
    "process_file",
    "process_folder",
    "process_one_file",
    "report_bound_hits",
    "rmse_complex",
    "save_fit_outputs",
    "save_outputs",
]
