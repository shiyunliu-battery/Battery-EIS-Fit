from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import least_squares

from .config import FitConfig, TailModel, parameter_names
from .model import model_eis, model_eis_step, rmse_complex


SUPPORTED_LOSSES = {"linear", "soft_l1", "huber", "cauchy", "arctan"}
SUPPORTED_WEIGHTS = {"modulus", "unit"}


@dataclass(frozen=True)
class FitResult:
    parameters: dict[str, float]
    p_opt: np.ndarray
    Zsim: np.ndarray
    rmse: float
    nrmse: float
    step_rmse: dict[int, float]
    step_nrmse: dict[int, float]
    bound_hits: list[str]
    tail: TailModel
    optimizer: Any


def estimate_tail(freq: np.ndarray, Zexp: np.ndarray) -> tuple[float, float, float]:
    try:
        n_tail = 6
        if len(freq) <= n_tail:
            return 1e-3, 0.8, 1e-2
        w_tail = 2 * np.pi * freq[-n_tail:]
        Z_tail = np.maximum(np.abs(Zexp[-n_tail:]), 1e-15)
        slope, intercept = np.polyfit(np.log(w_tail), np.log(Z_tail), 1)
        nd_guess = float(np.clip(-slope, 0.5, 1.0))
        Qd_guess = float(np.clip(np.exp(-intercept), 1e-5, 1e3))
        sigma_guess = float(np.clip(np.median(Z_tail * np.sqrt(w_tail)), 1e-8, 1e6))
        return Qd_guess, nd_guess, sigma_guess
    except (FloatingPointError, ValueError, np.linalg.LinAlgError):
        return 1e-3, 0.8, 1e-2


def prepare_eis_arrays(freq: np.ndarray, Zexp: np.ndarray, min_points: int = 5) -> tuple[np.ndarray, np.ndarray]:
    freq = np.asarray(freq, dtype=float).reshape(-1)
    Zexp = np.asarray(Zexp, dtype=complex).reshape(-1)

    if len(freq) != len(Zexp):
        raise ValueError("freq and Zexp must have the same length.")

    mask = np.isfinite(freq) & np.isfinite(Zexp.real) & np.isfinite(Zexp.imag) & (freq > 0)
    if np.count_nonzero(mask) < min_points:
        raise ValueError(f"At least {min_points} finite EIS points with positive frequency are required for fitting.")

    freq = freq[mask]
    Zexp = Zexp[mask]
    order = np.argsort(freq)[::-1]
    return freq[order], Zexp[order]


def validate_config(cfg: FitConfig) -> None:
    if cfg.tail not in {"cpe", "warburg"}:
        raise ValueError(f"Unsupported tail model: {cfg.tail}")
    if cfg.weight_func not in SUPPORTED_WEIGHTS:
        raise ValueError(f"Unsupported weight_func: {cfg.weight_func}. Expected one of {sorted(SUPPORTED_WEIGHTS)}.")
    if cfg.loss not in SUPPORTED_LOSSES:
        raise ValueError(f"Unsupported loss: {cfg.loss}. Expected one of {sorted(SUPPORTED_LOSSES)}.")
    if cfg.n_starts < 1:
        raise ValueError("n_starts must be at least 1.")
    if cfg.max_nfev < 1:
        raise ValueError("max_nfev must be at least 1.")
    if cfg.weight_eps <= 0:
        raise ValueError("weight_eps must be positive.")
    if cfg.f_scale is not None and cfg.f_scale <= 0:
        raise ValueError("f_scale must be positive when provided.")


def make_bounds_from_data(freq: np.ndarray, Zexp: np.ndarray, tail: TailModel = "cpe") -> tuple[np.ndarray, np.ndarray]:
    w = 2 * np.pi * np.asarray(freq, float)
    R0_hf = float(np.median(Zexp.real[: min(5, len(Zexp))]))
    Rmax_est = float(np.max(Zexp.real))
    R_span = max(Rmax_est - R0_hf, 1e-6)
    L_est = float(abs(Zexp.imag[0]) / max(w[0], 1e-12))

    L_lb = max(L_est / 100.0, 1e-11)
    L_ub = min(max(L_est * 100.0, L_lb * 10.0), 1e-2)
    R0_lb = max(R0_hf * 0.2, 1e-6)
    R0_ub = max(R0_hf * 5.0, 1e-4)
    R_limit = max(R_span * 1.5, 1e-2)
    Q_lb, Q_ub = 1e-10, 1e6
    n_lb, n_ub = 0.01, 1.0

    base_lb = [L_lb, R0_lb, 1e-7, Q_lb, n_lb, 1e-7, Q_lb, n_lb]
    base_ub = [L_ub, R0_ub, R_limit, Q_ub, n_ub, R_limit, Q_ub, n_ub]

    if tail == "cpe":
        lb = np.array([*base_lb, 1e-12, n_lb], float)
        ub = np.array([*base_ub, 1e10, n_ub], float)
    elif tail == "warburg":
        sigma_scale = max(float(np.median(np.abs(Zexp[-min(6, len(Zexp)) :]) * np.sqrt(w[-min(6, len(w)) :]))), 1e-8)
        lb = np.array([*base_lb, max(sigma_scale / 1e6, 1e-12)], float)
        ub = np.array([*base_ub, max(sigma_scale * 1e6, 1e-6)], float)
    else:
        raise ValueError(f"Unsupported tail model: {tail}")
    return lb, ub


def initial_guess(freq: np.ndarray, Zexp: np.ndarray, tail: TailModel = "cpe") -> np.ndarray:
    f_high = float(freq[0])
    R0_guess = float(np.nanmin(Zexp.real))
    L_guess = float(abs(Zexp.imag[0]) / (2 * np.pi * f_high))
    R_span = max(float(np.nanmax(Zexp.real)) - R0_guess, 1e-3)
    Qd_guess, nd_guess, sigma_guess = estimate_tail(freq, Zexp)

    base = [
        max(L_guess, 1e-9),
        max(R0_guess, 1e-5),
        max(R_span * 0.1, 1e-4),
        1e-3,
        0.85,
        max(R_span * 0.1, 1e-4),
        1e-3,
        0.9,
    ]
    if tail == "cpe":
        return np.array([*base, Qd_guess, nd_guess], dtype=float)
    if tail == "warburg":
        return np.array([*base, sigma_guess], dtype=float)
    raise ValueError(f"Unsupported tail model: {tail}")


def random_in_bounds(rng: np.random.Generator, lb: np.ndarray, ub: np.ndarray, tail: TailModel = "cpe") -> np.ndarray:
    p = np.empty_like(lb)
    exponent_idx = {4, 7, 9} if tail == "cpe" else {4, 7}
    for i in range(len(lb)):
        if i in exponent_idx:
            p[i] = rng.uniform(lb[i], ub[i])
        else:
            p[i] = np.exp(rng.uniform(np.log(lb[i]), np.log(ub[i])))
    return p


def get_bound_hits(p: np.ndarray, lb: np.ndarray, ub: np.ndarray, tail: TailModel = "cpe") -> list[str]:
    hits = []
    for name, val, lower, upper in zip(parameter_names(tail), p, lb, ub):
        if upper > lower * 100:
            is_low = val < lower * 1.1
            is_high = val > upper / 1.1
        else:
            tol = 0.01 * (upper - lower)
            is_low = val - lower < tol
            is_high = upper - val < tol
        if is_low:
            hits.append(f"{name} near lower bound ({val:.3e} ~ {lower:.3e})")
        elif is_high:
            hits.append(f"{name} near upper bound ({val:.3e} ~ {upper:.3e})")
    return hits


def fixed_bounds(cfg: FitConfig) -> tuple[np.ndarray, np.ndarray]:
    lb = np.array(cfg.lb, float)
    ub = np.array(cfg.ub, float)
    if cfg.tail == "warburg":
        if len(lb) == 10 and len(ub) == 10:
            lb = lb[[0, 1, 2, 3, 4, 5, 6, 7, 8]]
            ub = ub[[0, 1, 2, 3, 4, 5, 6, 7, 8]]
        elif len(lb) != 9 or len(ub) != 9:
            raise ValueError("Warburg fixed bounds must contain either 9 values or the default 10-value CPE-compatible bounds.")
    elif len(lb) != 10 or len(ub) != 10:
        raise ValueError("CPE fixed bounds must contain 10 values.")
    if lb.shape != ub.shape:
        raise ValueError("Lower and upper bounds must have the same length.")
    if np.any(~np.isfinite(lb)) or np.any(~np.isfinite(ub)):
        raise ValueError("Bounds must be finite.")
    if np.any(lb <= 0) or np.any(ub <= 0):
        raise ValueError("All bounds must be positive.")
    if np.any(lb >= ub):
        raise ValueError("Every lower bound must be smaller than its upper bound.")
    return lb, ub


def fit_model_eis(freq: np.ndarray, Zexp: np.ndarray, cfg: FitConfig = FitConfig()) -> FitResult:
    validate_config(cfg)
    freq, Zexp = prepare_eis_arrays(freq, Zexp)

    w = 2 * np.pi * freq
    wt = 1.0 / np.maximum(np.abs(Zexp), cfg.weight_eps) if cfg.weight_func == "modulus" else np.ones_like(Zexp, dtype=float)
    lb, ub = make_bounds_from_data(freq, Zexp, cfg.tail) if cfg.use_adaptive_bounds else fixed_bounds(cfg)

    f_scale = cfg.f_scale
    if cfg.loss != "linear" and f_scale is None:
        f_scale = max(0.15 * float(np.median(np.abs(Zexp))), cfg.weight_eps) if cfg.weight_func == "unit" else 0.05
    if f_scale is None:
        f_scale = 1.0

    def residual(p: np.ndarray) -> np.ndarray:
        Zm = model_eis(p, w, tail=cfg.tail)
        return np.concatenate([(Zm.real - Zexp.real) * wt, (Zm.imag - Zexp.imag) * wt])

    p0 = np.clip(initial_guess(freq, Zexp, cfg.tail), lb * (1 + 1e-12), ub * (1 - 1e-12))
    rng = np.random.default_rng(cfg.seed)
    best = None

    for k in range(cfg.n_starts):
        pstart = p0 if k == 0 else random_in_bounds(rng, lb, ub, cfg.tail)
        pstart = np.clip(pstart, lb * (1 + 1e-12), ub * (1 - 1e-12))
        res = least_squares(residual, pstart, bounds=(lb, ub), max_nfev=cfg.max_nfev, loss=cfg.loss, f_scale=f_scale)
        if best is None or res.cost < best.cost:
            best = res

    if best is None:
        raise RuntimeError("Optimizer did not run. Check n_starts and fitting configuration.")

    p_opt = best.x
    Zsim = model_eis(p_opt, w, tail=cfg.tail)
    rmse = rmse_complex(Zsim, Zexp)
    median_Z = float(max(np.median(np.abs(Zexp)), cfg.weight_eps))
    step_rmse = {step: rmse_complex(model_eis_step(p_opt, w, step, tail=cfg.tail), Zexp) for step in (1, 2, 3, 4)}
    step_nrmse = {step: value / median_Z for step, value in step_rmse.items()}

    return FitResult(
        parameters=dict(zip(parameter_names(cfg.tail), map(float, p_opt))),
        p_opt=p_opt,
        Zsim=Zsim,
        rmse=rmse,
        nrmse=rmse / median_Z,
        step_rmse=step_rmse,
        step_nrmse=step_nrmse,
        bound_hits=get_bound_hits(p_opt, lb, ub, cfg.tail),
        tail=cfg.tail,
        optimizer=best,
    )
