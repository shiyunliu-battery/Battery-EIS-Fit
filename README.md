# eisfit

`eisfit` is an open-source Python package for fitting electrochemical impedance spectroscopy (EIS) data and identifying equivalent-circuit parameters.

The base model is:

```text
Z = jωL + R0 + (R1 || CPE1) + (R2 || CPE2) + tail
```

Two low-frequency tail models are available:

```text
CPE tail, default:       tail = 1 / (Qd * (jω)^nd)
Warburg tail:            tail = σ / sqrt(jω)
```

The CPE version keeps `Qd` and `nd` free. The Warburg version is the traditional semi-infinite Warburg form, equivalent to a CPE exponent fixed at `n = 0.5` with a single fitted coefficient `σ`.

CPE parameters:

```text
[L, R0, R1, Q1, n1, R2, Q2, n2, Qd, nd]
```

Warburg parameters:

```text
[L, R0, R1, Q1, n1, R2, Q2, n2, sigma]
```

## Features

- CSV and Excel EIS data loading with flexible column matching
- Multi-start bounded least-squares fitting
- Robust loss and impedance-modulus weighting options
- Python functions and command-line interface
- Excel/PNG output generation for local analysis
- Public demo notebook for the Zenodo-derived repository dataset

## Dataset attribution

The repository `EIS_dataset` example files are from:

> M. Moertelmaier, M. Kasper, and S. Clark, "EIS data of 54 21700 cells", Zenodo, May 26, 2025. doi: 10.5281/zenodo.15422339.

The included metadata reports a CC-BY 4.0 license for the dataset. Keep this attribution if you redistribute the data.
The PyPI package distributions intentionally do not bundle the dataset; use your own EIS files after installation.

## Installation

After PyPI release:

```bash
pip install eisfit
```

For local development:

```bash
pip install -e ".[dev]"
```

Minimal package only:

```bash
pip install -e .
```

## Python usage

Simple array-based use:

```python
from eisfit import fit, load_eis

freq, Zexp = load_eis("my_eis.csv")

cpe = fit(freq, Zexp)                  # default tail="cpe"
warburg = fit(freq, Zexp, tail="warburg")

print(cpe.parameters)
print(cpe.rmse, cpe.nrmse)
```

One-line file-based use:

```python
from eisfit import fit_file

result = fit_file("my_eis.csv", tail="cpe")
warburg = fit_file("my_eis.csv", tail="warburg")
```

Advanced use with full configuration:

```python
from eisfit import FitConfig, fit_model_eis, load_eis

freq, Zexp = load_eis("my_eis.csv")
cfg = FitConfig(tail="cpe", n_starts=80, seed=7, max_nfev=8000)
result = fit_model_eis(freq, Zexp, cfg=cfg)
```

## Command-line usage

Fit one file with the default CPE tail and write Excel/PNG outputs:

```bash
eisfit my_eis.csv --out-dir outputs --n-starts 40
```

Fit the same file with a semi-infinite Warburg tail:

```bash
eisfit my_eis.csv --tail warburg --out-dir outputs --n-starts 40
```

Batch fit a folder:

```bash
eisfit my_eis_folder --pattern "*.csv" --out-dir outputs --n-starts 20
```

## Public notebook

Use `examples/demo_fit_zenodo_dataset.ipynb` with the repository dataset for a clean public demo.

## Development checks

```bash
pytest
python -m compileall src tests
```

## License

Package code is released under the MIT License. Dataset files retain their original dataset license and attribution requirements.
