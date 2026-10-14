# Changelog

## 0.2.0 — 2026-10-14

- Record each optimizer start's start parameters (solver order) and final
  parameters in the reported characteristic-time order, with the start's
  parameter permutation and bound hits. Non-finite values are recorded as
  `None`, so attempts and convergence errors remain valid JSON.
- Report near-best starts in `diagnostics["near_best"]`: accepted starts whose
  cost is within `FitConfig.near_best_rtol` (default 0.01) of the best, with
  per-parameter ranges. This describes the optimizer run; it does not establish
  identifiability or uncertainty.
- Provide parameter units through `PARAMETER_UNITS`, `parameter_units(tail)`,
  `FitResult.parameter_units`, the diagnostics and the saved diagnostics JSON.
- Add `model_impedance(parameters, frequency_hz, tail)` to evaluate the circuit
  from named parameters at any frequency.
- **Breaking:** move figure options out of `FitConfig` into `PlotConfig(dpi, close)`,
  passed to `save_fit_outputs`, `process_file` and `process_folder`. The
  `save_png_dpi`, `show_plot` and `close_plot` fields are removed; `show_plot`
  was never used.
- Add an `attempt_parameters` sheet to the Excel output; the attempts sheet keeps
  scalar columns only.
- Release from `main` by version tag; the GitHub release carries this version's
  changelog section.

## 0.1.1

- Select only converged optimizer starts with finite results. Raise
  `FitConvergenceError` with per-start diagnostics when none are accepted.
- Order the two R-CPE branches by increasing characteristic time, retaining
  the original solver order and an explicit parameter permutation.
- Remap effective bounds and bound warnings with the reported branch order.
- Export solver diagnostics and the actual fit configuration to JSON, with
  optimizer attempts included in Excel outputs.
- Return a nonzero CLI exit status for failed fits while continuing folder
  processing after individual failures.
- Add regression tests and CI for Python 3.10, 3.11 and 3.12.

Convergence and branch ordering do not establish parameter identifiability or
persistent physical-process identity across spectra.
