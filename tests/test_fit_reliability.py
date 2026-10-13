from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from eisfit import FitConfig, FitConvergenceError, fit, fit_file, fit_model_eis, model_eis, process_folder
from eisfit import fitting
from eisfit.cli import main


def spectrum(tail="cpe"):
    freq = np.logspace(4, -1, 32)
    # Arc 1 has a longer characteristic time than arc 2.
    p = np.array([1e-7, 0.014, 0.003, 3.0, 0.82, 0.0015, 1.2, 0.9, 700.0, 0.55])
    if tail == "warburg":
        p = np.r_[p[:8], 0.002]
    return freq, p, model_eis(p, 2 * np.pi * freq, tail=tail)


def solver_result(p, *, success=True, cost=1.0):
    return SimpleNamespace(x=p.copy(), success=success, cost=cost, fun=np.zeros(64),
                           status=1 if success else 0, message="converged" if success else "evaluation limit", nfev=5)


def write_csv(path, freq, z):
    pd.DataFrame({"Frequency_Hz": freq, "Real_Ohm": z.real, "Imag_Ohm": z.imag}).to_csv(path, index=False)


def test_evaluation_limit_raises_with_auditable_attempts():
    freq, _, z = spectrum()
    with pytest.raises(FitConvergenceError) as caught:
        fit(freq, z, n_starts=2, max_nfev=1)
    assert len(caught.value.attempts) == 2
    assert all(not a.accepted and not a.optimizer_success and a.status == 0 for a in caught.value.attempts)
    assert all(a.rejection_reason == "optimizer_not_converged" for a in caught.value.attempts)


def test_failed_lower_cost_start_cannot_displace_converged_start(monkeypatch):
    freq, p, z = spectrum()
    outcomes = iter([solver_result(p, success=False, cost=0.0), solver_result(p, cost=1.0)])
    monkeypatch.setattr(fitting, "least_squares", lambda *args, **kwargs: next(outcomes))
    result = fit(freq, z, n_starts=2)
    assert result.selected_start_index == 1
    assert [a.accepted for a in result.attempts] == [False, True]
    assert result.optimizer.success
    assert result.diagnostics["accepted_start_count"] == 1


def test_lowest_cost_accepted_start_is_selected(monkeypatch):
    freq, p, z = spectrum()
    outcomes = iter([solver_result(p, cost=2.0), solver_result(p, cost=1.0)])
    monkeypatch.setattr(fitting, "least_squares", lambda *args, **kwargs: next(outcomes))
    result = fit(freq, z, n_starts=2)
    assert result.selected_start_index == 1
    assert result.optimizer.cost == 1.0


@pytest.mark.parametrize("invalid", ["cost", "parameters", "residuals"])
def test_nonfinite_successful_solver_result_is_rejected(monkeypatch, invalid):
    freq, p, z = spectrum()
    outcome = solver_result(p)
    if invalid == "cost":
        outcome.cost = np.nan
    elif invalid == "parameters":
        outcome.x[2] = np.nan
    else:
        outcome.fun[0] = np.inf
    monkeypatch.setattr(fitting, "least_squares", lambda *args, **kwargs: outcome)
    with pytest.raises(FitConvergenceError) as caught:
        fit(freq, z, n_starts=1)
    attempt = caught.value.attempts[0]
    assert attempt.optimizer_success and not attempt.accepted
    assert attempt.rejection_reason == "non_finite_optimizer_result"
    if invalid == "cost":
        assert attempt.cost is None


@pytest.mark.parametrize("tail", ["cpe", "warburg"])
def test_swapped_arcs_have_identical_reported_parameters_and_spectrum(monkeypatch, tail):
    freq, p, z = spectrum(tail)
    swapped = p.copy()
    swapped[2:5], swapped[5:8] = p[5:8], p[2:5]
    outcomes = iter([solver_result(p), solver_result(swapped)])
    monkeypatch.setattr(fitting, "least_squares", lambda *args, **kwargs: next(outcomes))
    first = fit(freq, z, tail=tail, n_starts=1)
    second = fit(freq, z, tail=tail, n_starts=1)
    assert first.parameters == second.parameters
    np.testing.assert_allclose(first.Zsim, z, rtol=1e-12, atol=1e-15)
    np.testing.assert_allclose(second.Zsim, z, rtol=1e-12, atol=1e-15)
    np.testing.assert_array_equal(first.p_opt, first.optimizer.x[list(first.parameter_permutation)])
    np.testing.assert_array_equal(first.optimizer.x, p)  # raw SciPy order is retained
    log_tau1 = np.log(first.parameters["R1_Ohm"] * first.parameters["Q1"]) / first.parameters["n1"]
    log_tau2 = np.log(first.parameters["R2_Ohm"] * first.parameters["Q2"]) / first.parameters["n2"]
    assert log_tau1 <= log_tau2


def test_exact_characteristic_time_tie_has_deterministic_labels(monkeypatch):
    freq, p, _ = spectrum()
    p[2:8] = [0.004, 0.25, 1.0, 0.002, 0.5, 1.0]
    z = model_eis(p, 2 * np.pi * freq)
    swapped = p.copy()
    swapped[2:5], swapped[5:8] = p[5:8], p[2:5]
    outcomes = iter([solver_result(p), solver_result(swapped)])
    monkeypatch.setattr(fitting, "least_squares", lambda *args, **kwargs: next(outcomes))
    first = fit(freq, z, n_starts=1)
    second = fit(freq, z, n_starts=1)
    assert first.parameters == second.parameters


def test_bound_diagnostics_follow_relabelled_arcs(monkeypatch):
    freq, p, z = spectrum()
    lower = np.array([1e-9, 0.001, 0.001, 0.01, 0.1, 0.0001, 0.01, 0.1, 1.0, 0.1])
    upper = np.array([1e-5, 0.1, 0.003, 10.0, 1.0, 0.01, 10.0, 1.0, 1000.0, 1.0])
    monkeypatch.setattr(fitting, "least_squares", lambda *args, **kwargs: solver_result(p))
    result = fit_model_eis(freq, z, FitConfig(n_starts=1, use_adaptive_bounds=False, lb=tuple(lower), ub=tuple(upper)))
    assert result.parameter_permutation[5] == 2
    assert result.parameter_bounds["R2_Ohm"] == (0.001, 0.003)
    assert any(hit.startswith("R2_Ohm near upper bound") for hit in result.bound_hits)
    assert not any(hit.startswith("R1_Ohm near upper bound") for hit in result.bound_hits)


def test_failed_file_fit_writes_no_fit_outputs(tmp_path):
    freq, _, z = spectrum()
    source = tmp_path / "sample.csv"
    write_csv(source, freq, z)
    output = tmp_path / "failed_outputs"
    with pytest.raises(FitConvergenceError):
        fit_file(source, n_starts=1, max_nfev=1, out_dir=output)
    assert not output.exists()


def test_file_export_retains_diagnostics_and_actual_configuration(tmp_path, monkeypatch):
    freq, p, z = spectrum("warburg")
    monkeypatch.setattr(fitting, "least_squares", lambda *args, **kwargs: solver_result(p))
    source = tmp_path / "sample.csv"
    write_csv(source, freq, z)
    output = tmp_path / "out"
    result = fit_file(source, tail="warburg", n_starts=1, seed=17, max_nfev=30, weight="unit", out_dir=output)
    payload = json.loads((output / "sample_warburg_fit_diagnostics.json").read_text())
    assert payload["parameters"] == result.parameters
    assert payload["diagnostics"]["optimizer_success"]
    assert payload["diagnostics"]["identifiability_status"] == "not_assessed"
    assert payload["config"]["tail"] == "warburg"
    assert payload["config"]["seed"] == 17
    assert payload["config"]["weight_func"] == "unit"
    attempts = pd.read_excel(output / "sample_warburg_eisfit.xlsx", sheet_name="optimizer_attempts")
    assert len(attempts) == 1 and attempts.loc[0, "accepted"]


@pytest.mark.parametrize("folder", [False, True])
def test_cli_failure_is_machine_readable_and_nonzero(tmp_path, capsys, folder):
    freq, _, z = spectrum()
    source = tmp_path / "sample.csv"
    write_csv(source, freq, z)
    output = tmp_path / "failed_outputs"
    code = main([str(tmp_path if folder else source), "--out-dir", str(output), "--n-starts", "1", "--max-nfev", "1"])
    payload = json.loads(capsys.readouterr().out)
    failure = payload[str(source)] if folder else payload
    assert code == 1
    assert failure["error_type"] == "FitConvergenceError"
    assert failure["attempts"][0]["rejection_reason"] == "optimizer_not_converged"
    assert not output.exists()


def test_folder_continues_after_a_failed_fit(tmp_path, monkeypatch):
    freq, p, z = spectrum()
    write_csv(tmp_path / "a.csv", freq, z)
    write_csv(tmp_path / "b.csv", freq, z)
    outcomes = iter([solver_result(p, success=False), solver_result(p)])
    monkeypatch.setattr(fitting, "least_squares", lambda *args, **kwargs: next(outcomes))
    results = process_folder(tmp_path, cfg=FitConfig(n_starts=1))
    assert results[str(tmp_path / "a.csv")]["error_type"] == "FitConvergenceError"
    assert results[str(tmp_path / "b.csv")]["fit"].optimizer.success
