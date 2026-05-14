from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd


def find_column(columns, candidates: list[list[str]]):
    original = list(columns)
    normalized = [str(c).lower().strip() for c in original]
    for keyset in candidates:
        for i, column in enumerate(normalized):
            if all(key.lower() in column for key in keyset):
                return original[i]
    return None


def load_eis(path: str | Path, sheet_name: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray]:
    path = Path(path)
    suffix = path.suffix.lower()

    try:
        if suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(path, sheet_name=sheet_name)
            if isinstance(df, dict):
                if not df:
                    raise ValueError(f"No sheets found in Excel file: {path.name}")
                df = df[next(iter(df))]
        elif suffix == ".csv":
            df = pd.read_csv(path)
        else:
            raise ValueError(f"Unsupported EIS file type: {suffix}. Use CSV or Excel.")
    except (OSError, ValueError, pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        raise ValueError(f"Could not read EIS file {path.name}: {exc}") from exc

    c_freq = find_column(df.columns, [["frequency"], ["freq"], ["freq. /hz"]])
    c_zre = find_column(df.columns, [["real"], ["zre"], ["z1"], ["z'"], ["z1 /ohm"]])
    c_zim = find_column(df.columns, [["imag"], ["zim"], ["z2"], ["z''"], ["z2 /ohm"]])

    if c_freq is None or c_zre is None or c_zim is None:
        raise ValueError(
            f"Could not infer EIS columns in {path.name}. Found columns: {list(df.columns)}. "
            "Expected frequency, real impedance, and imaginary impedance columns."
        )

    freq = pd.to_numeric(df[c_freq], errors="coerce").to_numpy(dtype=float)
    zre = pd.to_numeric(df[c_zre], errors="coerce").to_numpy(dtype=float)
    zim = pd.to_numeric(df[c_zim], errors="coerce").to_numpy(dtype=float)

    mask = np.isfinite(freq) & np.isfinite(zre) & np.isfinite(zim) & (freq > 0)
    if not np.any(mask):
        raise ValueError(f"No valid EIS rows found in {path.name}.")

    freq = freq[mask]
    Zexp = (zre[mask] + 1j * zim[mask]).astype(complex)
    order = np.argsort(freq)[::-1]
    return freq[order], Zexp[order]


def eis_dataframe(freq: np.ndarray, Zexp: np.ndarray, Zsim: np.ndarray | None = None) -> pd.DataFrame:
    data = {
        "Frequency_Hz": freq,
        "Zre_exp_Ohm": Zexp.real,
        "Zim_exp_Ohm": Zexp.imag,
        "-Zim_exp_Ohm": -Zexp.imag,
        "Phase_exp_deg": np.angle(Zexp, deg=True),
        "-Phase_exp_deg": -np.angle(Zexp, deg=True),
    }
    if Zsim is not None:
        data.update(
            {
                "Zre_sim_Ohm": Zsim.real,
                "Zim_sim_Ohm": Zsim.imag,
                "-Zim_sim_Ohm": -Zsim.imag,
                "Phase_sim_deg": np.angle(Zsim, deg=True),
                "-Phase_sim_deg": -np.angle(Zsim, deg=True),
            }
        )
    return pd.DataFrame(data)
