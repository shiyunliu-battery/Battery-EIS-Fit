from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from .config import FitConfig
from .fitting import FitResult, fit_model_eis
from .io import eis_dataframe, load_eis
from .plotting import plot_fit


def save_fit_outputs(input_path: str | Path, freq, Zexp, fit: FitResult, out_dir: str | Path, cfg: FitConfig = FitConfig()) -> dict[str, str]:
    input_path = Path(input_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    base = input_path.stem
    out_xlsx = out_dir / f"{base}_{fit.tail}_eisfit.xlsx"
    out_png = out_dir / f"{base}_{fit.tail}_eisfit.png"

    df_fit = eis_dataframe(freq, Zexp, fit.Zsim)
    df_params = pd.DataFrame({"Parameter": list(fit.parameters.keys()), "Value": list(fit.parameters.values())})
    df_metrics = pd.DataFrame(
        {
            "Metric": ["RMSE_full", "NRMSE_full", "RMSE_step1", "RMSE_step2", "RMSE_step3", "RMSE_step4", "NRMSE_step1", "NRMSE_step2", "NRMSE_step3", "NRMSE_step4"],
            "Value": [
                fit.rmse,
                fit.nrmse,
                fit.step_rmse[1],
                fit.step_rmse[2],
                fit.step_rmse[3],
                fit.step_rmse[4],
                fit.step_nrmse[1],
                fit.step_nrmse[2],
                fit.step_nrmse[3],
                fit.step_nrmse[4],
            ],
        }
    )
    df_bounds = pd.DataFrame({"BoundHit": fit.bound_hits})

    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        df_fit.to_excel(writer, sheet_name="fit_data", index=False)
        df_params.to_excel(writer, sheet_name="parameters", index=False)
        df_metrics.to_excel(writer, sheet_name="metrics", index=False)
        df_bounds.to_excel(writer, sheet_name="bound_hits", index=False)

    fig = plot_fit(freq, Zexp, fit.Zsim, output_path=out_png, dpi=cfg.save_png_dpi)
    if cfg.close_plot:
        import matplotlib.pyplot as plt

        plt.close(fig)

    return {"xlsx": str(out_xlsx), "png": str(out_png)}


def process_file(path: str | Path, cfg: FitConfig = FitConfig(), out_dir: Optional[str | Path] = None, sheet_name: Optional[str] = None) -> dict:
    freq, Zexp = load_eis(path, sheet_name=sheet_name)
    fit = fit_model_eis(freq, Zexp, cfg=cfg)
    outputs = None
    if out_dir is not None:
        outputs = save_fit_outputs(path, freq, Zexp, fit, out_dir=out_dir, cfg=cfg)
    return {"input_path": str(path), "freq": freq, "Zexp": Zexp, "fit": fit, "outputs": outputs}


def process_folder(folder: str | Path, pattern: str = "*.csv", cfg: FitConfig = FitConfig(), out_dir: Optional[str | Path] = None) -> dict[str, dict]:
    folder = Path(folder)
    paths = sorted(folder.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"No files matched: {folder / pattern}")
    results = {}
    for path in paths:
        try:
            results[str(path)] = process_file(path, cfg=cfg, out_dir=out_dir)
        except Exception as exc:
            results[str(path)] = {"error": repr(exc)}
    return results
