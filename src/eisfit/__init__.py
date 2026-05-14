from importlib.metadata import PackageNotFoundError, version

from .config import FitConfig, PARAMETER_NAMES, PARAMETER_NAMES_CPE, PARAMETER_NAMES_WARBURG, TailModel, parameter_names
from .fitting import FitResult, fit_model_eis
from .interface import fit, fit_file
from .io import load_eis
from .model import model_eis, model_eis_step, rmse_complex, z_warburg
from .pipeline import process_file, process_folder, save_fit_outputs

try:
    __version__ = version("eisfit")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = [
    "FitConfig",
    "FitResult",
    "PARAMETER_NAMES",
    "PARAMETER_NAMES_CPE",
    "PARAMETER_NAMES_WARBURG",
    "TailModel",
    "__version__",
    "fit",
    "fit_file",
    "fit_model_eis",
    "load_eis",
    "model_eis",
    "model_eis_step",
    "parameter_names",
    "process_file",
    "process_folder",
    "rmse_complex",
    "save_fit_outputs",
    "z_warburg",
]
