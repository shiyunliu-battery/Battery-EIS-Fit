# Changelog

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
