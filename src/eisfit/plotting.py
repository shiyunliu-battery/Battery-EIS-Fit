from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def plot_fit(freq: np.ndarray, Zexp: np.ndarray, Zsim: np.ndarray, output_path: str | Path | None = None, dpi: int = 300):
    phase_exp = np.angle(Zexp, deg=True)
    phase_sim = np.angle(Zsim, deg=True)
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), constrained_layout=True)

    ax = axes[0]
    ax.plot(Zexp.real, -Zexp.imag, marker="o", linestyle="None", markersize=3, label="Experiment")
    ax.plot(Zsim.real, -Zsim.imag, linestyle="-", label="Model")
    ax.set_xlabel("Z' (Ω)")
    ax.set_ylabel("-Z'' (Ω)")
    ax.set_title("Nyquist")
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False)

    ax = axes[1]
    ax.semilogx(freq, -phase_exp, marker="o", linestyle="None", markersize=3, label="Experiment")
    ax.semilogx(freq, -phase_sim, linestyle="-", label="Model")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("-Phase (deg)")
    ax.set_title("Phase")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(frameon=False)

    ax = axes[2]
    ax.semilogx(freq, Zexp.real, marker="o", linestyle="None", markersize=3, label="Experiment")
    ax.semilogx(freq, Zsim.real, linestyle="-", label="Model")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Z' (Ω)")
    ax.set_title("Real impedance")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(frameon=False)

    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    if output_path is not None:
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    return fig
