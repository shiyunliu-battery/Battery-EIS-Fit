from importlib.metadata import PackageNotFoundError, version

from .config import (
    PARAMETER_NAMES,
    PARAMETER_NAMES_CPE,
    PARAMETER_NAMES_WARBURG,
    PARAMETER_UNITS,
    FitConfig,
    PlotConfig,
    TailModel,
    parameter_names,
    parameter_units,
)
from .fitting import FitAttempt, FitConvergenceError, FitResult, fit_model_eis
from .interface import fit, fit_file
from .io import load_eis
from .model import model_eis, model_eis_step, model_impedance, rmse_complex, z_warburg
from .pipeline import process_file, process_folder, save_fit_outputs

try:
    __version__ = version("eisfit")
except PackageNotFoundError:  # source tree without installed metadata
    __version__ = "0+unknown"

__all__ = [
    "FitConfig",
    "FitAttempt",
    "FitConvergenceError",
    "FitResult",
    "PARAMETER_NAMES",
    "PARAMETER_NAMES_CPE",
    "PARAMETER_NAMES_WARBURG",
    "PARAMETER_UNITS",
    "PlotConfig",
    "TailModel",
    "__version__",
    "fit",
    "fit_file",
    "fit_model_eis",
    "load_eis",
    "model_eis",
    "model_eis_step",
    "model_impedance",
    "parameter_names",
    "parameter_units",
    "process_file",
    "process_folder",
    "rmse_complex",
    "save_fit_outputs",
    "z_warburg",
]
