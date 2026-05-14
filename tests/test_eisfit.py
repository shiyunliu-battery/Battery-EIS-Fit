from __future__ import annotations

import numpy as np
import pytest

from eisfit import fit, fit_file, load_eis, model_eis, parameter_names


def sample_eis():
    freq = np.logspace(4, -1, 32)
    w = 2 * np.pi * freq
    p = np.array([1e-7, 0.014, 0.003, 0.7, 0.82, 0.0015, 1.2, 0.9, 700.0, 0.55])
    return freq, model_eis(p, w, tail="cpe")


def write_sample_csv(path, freq=None, Zexp=None):
    if freq is None or Zexp is None:
        freq, Zexp = sample_eis()
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("Frequency_Hz,Real_Ohm,Imag_Ohm\n")
        for f_value, z_value in zip(freq, Zexp):
            handle.write(f"{f_value},{z_value.real},{z_value.imag}\n")


def test_load_public_csv_dataset(tmp_path):
    path = tmp_path / "sample.csv"
    freq, Zexp = sample_eis()
    write_sample_csv(path, freq=freq[::-1], Zexp=Zexp[::-1])

    loaded_freq, loaded_Zexp = load_eis(path)

    assert len(loaded_freq) == len(loaded_Zexp)
    assert len(loaded_freq) > 10
    assert np.all(loaded_freq > 0)
    assert np.all(np.diff(loaded_freq) <= 0)


def test_model_returns_complex_array_for_cpe_tail():
    freq = np.array([1000.0, 100.0, 10.0])
    w = 2 * np.pi * freq
    p = np.array([1e-7, 0.01, 0.01, 1e-3, 0.8, 0.02, 1e-3, 0.9, 1e-2, 0.7])
    Z = model_eis(p, w, tail="cpe")
    assert Z.shape == freq.shape
    assert np.iscomplexobj(Z)


def test_model_returns_complex_array_for_warburg_tail():
    freq = np.array([1000.0, 100.0, 10.0])
    w = 2 * np.pi * freq
    p = np.array([1e-7, 0.01, 0.01, 1e-3, 0.8, 0.02, 1e-3, 0.9, 0.02])
    Z = model_eis(p, w, tail="warburg")
    assert Z.shape == freq.shape
    assert np.iscomplexobj(Z)


def test_simple_fit_api_uses_cpe_tail_by_default():
    freq, Zexp = sample_eis()
    result = fit(freq, Zexp, n_starts=1, max_nfev=200, seed=1)
    assert set(result.parameters) == set(parameter_names("cpe"))
    assert result.tail == "cpe"
    assert np.isfinite(result.rmse)
    assert np.isfinite(result.nrmse)
    assert result.Zsim.shape == Zexp.shape


def test_simple_fit_api_supports_warburg_tail():
    freq, Zexp = sample_eis()
    result = fit(freq, Zexp, tail="warburg", n_starts=1, max_nfev=200, seed=1)
    assert set(result.parameters) == set(parameter_names("warburg"))
    assert result.tail == "warburg"
    assert "sigma" in result.parameters
    assert np.isfinite(result.rmse)
    assert np.isfinite(result.nrmse)
    assert result.Zsim.shape == Zexp.shape


def test_fit_sorts_array_inputs_before_fitting():
    freq, Zexp = sample_eis()
    descending = fit(freq, Zexp, n_starts=1, max_nfev=200, seed=1)
    ascending = fit(freq[::-1], Zexp[::-1], n_starts=1, max_nfev=200, seed=1)

    assert np.allclose(descending.p_opt, ascending.p_opt)
    assert descending.rmse == pytest.approx(ascending.rmse)


def test_fit_rejects_invalid_configuration_values():
    freq, Zexp = sample_eis()
    with pytest.raises(ValueError, match="n_starts"):
        fit(freq, Zexp, n_starts=0)
    with pytest.raises(ValueError, match="weight_func"):
        fit(freq, Zexp, weight="typo")
    with pytest.raises(ValueError, match="loss"):
        fit(freq, Zexp, loss="typo")


def test_fit_rejects_nonpositive_or_nonfinite_frequency():
    freq, Zexp = sample_eis()
    bad_freq = freq.copy()
    bad_freq[:28] = np.nan
    bad_freq[28:] = 0.0

    with pytest.raises(ValueError, match="positive frequency"):
        fit(bad_freq, Zexp)


def test_fit_file_api_loads_and_fits_csv(tmp_path):
    path = tmp_path / "sample.csv"
    write_sample_csv(path)

    result = fit_file(path, n_starts=1, max_nfev=200, seed=1)

    assert result.tail == "cpe"
    assert np.isfinite(result.rmse)
