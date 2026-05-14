# eisfit

`eisfit` is a lightweight Python package for fitting electrochemical impedance spectroscopy (EIS) data and extracting equivalent-circuit parameters.

The package supports a two-arc equivalent circuit with either a CPE-type low-frequency tail or a semi-infinite Warburg tail:

```text
Z = jωL + R0 + (R1 || CPE1) + (R2 || CPE2) + tail
```

It is designed for battery EIS analysis workflows where users need a simple Python API, a command-line tool, and reproducible fitted outputs.

## Features

- Load EIS data from CSV, XLS, and XLSX files
- Fit complex impedance data with bounded multi-start least squares
- Use either a flexible CPE tail or a Warburg diffusion tail
- Export fitted parameters, simulated impedance, residuals, and Nyquist plots
- Run from Python notebooks, scripts, or the command line
- Use included demo files to test the workflow immediately after cloning

## Installation

Install the released package from PyPI:

```bash
pip install eisfit
```

For local development from a cloned repository:

```bash
pip install -e ".[dev]"
```

## Quick Start

Fit one EIS file directly:

```python
from eisfit import fit_file

result = fit_file("my_eis.csv", tail="cpe", n_starts=40)

print(result.parameters)
print(result.rmse, result.nrmse)
```

Load the data first when you want direct access to frequency and impedance arrays:

```python
from eisfit import fit, load_eis

freq, Zexp = load_eis("my_eis.csv")
result = fit(freq, Zexp, tail="warburg")

print(result.parameters)
```

`freq` is the frequency array in Hz. `Zexp` is the measured complex impedance array:

```text
Zexp = Zreal + 1j * Zimag
```

## Input Data

Input files should contain at least three columns:

| Quantity | Meaning |
| --- | --- |
| frequency | Frequency in Hz |
| real impedance | Real part of impedance, usually `Zreal` or `Zre` |
| imaginary impedance | Imaginary part of impedance, usually `Zimag` or `Zim` |

Extra columns are allowed. `eisfit` tries to infer common column names automatically.

Example CSV:

```csv
Frequency_Hz,Zreal_Ohm,Zimag_Ohm
100000,0.0182,-0.0014
79432.8,0.0184,-0.0017
63100,0.0187,-0.0021
```

## Models

Default CPE-tail model:

```text
tail = 1 / (Qd * (jω)^nd)
parameters = [L, R0, R1, Q1, n1, R2, Q2, n2, Qd, nd]
```

Warburg-tail model:

```text
tail = σ / sqrt(jω)
parameters = [L, R0, R1, Q1, n1, R2, Q2, n2, sigma]
```

The CPE tail keeps the diffusion-like exponent free. The Warburg tail uses the traditional semi-infinite Warburg form.

## Command Line

Fit one file:

```bash
eisfit my_eis.csv --out-dir outputs --n-starts 40
```

Use the Warburg tail:

```bash
eisfit my_eis.csv --tail warburg --out-dir outputs --n-starts 40
```

Fit all matching files in a folder:

```bash
eisfit my_eis_folder --pattern "*.csv" --out-dir outputs --n-starts 20
```

## Outputs

For each fitted file, `eisfit` can generate:

- fitted equivalent-circuit parameters
- simulated impedance values
- residuals between measured and fitted impedance
- Nyquist plot PNG
- Excel output table for downstream analysis

## Demo

The repository includes example EIS files and a demo notebook:

```text
examples/demo_fit_zenodo_dataset.ipynb
```

You can run the notebook after installing the local development environment:

```bash
pip install -e ".[dev]"
jupyter notebook
```

## Development

Run the test suite:

```bash
pytest
```

Run a basic import/compile check:

```bash
python -m compileall src tests
```

Build the package locally:

```bash
python -m build
```

## Release

PyPI releases are built from the clean public package branch using GitHub Actions and Trusted Publishing. See `RELEASE.md` for the release workflow.

## License

The package code is released under the MIT License.
