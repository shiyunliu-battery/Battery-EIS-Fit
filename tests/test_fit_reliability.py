from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from eisfit import (
    FitConfig,
    FitConvergenceError,
    PlotConfig,
    fit,
    fit_file,
    fit_model_eis,
    model_eis,
    model_impedance,
    parameter_names,
    parameter_units,
    process_file,
    process_folder,
)
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
    if invalid == "parameters":
        assert attempt.parameters["R1_Ohm"] is None
    json.dumps([dataclasses.asdict(a) for a in caught.value.attempts], allow_nan=False)


def test_attempts_record_start_and_reported_final_parameters():
    freq, _, z = spectrum()
    result = fit(freq, z, n_starts=3, seed=3)
    names = parameter_names("cpe")
    assert all(list(a.start_parameters) == names and list(a.parameters) == names for a in result.attempts)
    selected = result.attempts[result.selected_start_index]
    assert selected.parameters == result.parameters
    assert selected.parameter_permutation == result.parameter_permutation
    json.dumps(result.diagnostics, allow_nan=False)


def test_attempt_parameters_use_the_reported_arc_order(monkeypatch):
    freq, p, z = spectrum()
    swapped = p.copy()
    swapped[2:5], swapped[5:8] = p[5:8], p[2:5]
    outcomes = iter([solver_result(p), solver_result(swapped)])
    monkeypatch.setattr(fitting, "least_squares", lambda *args, **kwargs: next(outcomes))
    first, second = fit(freq, z, n_starts=2).attempts
    assert first.parameters == second.parameters
    assert first.parameter_permutation != second.parameter_permutation


@pytest.mark.parametrize("rtol, expected", [(0.01, [0, 1]), (0.0, [0])])
def test_near_best_reports_starts_within_the_declared_cost_tolerance(monkeypatch, rtol, expected):
    freq, p, z = spectrum()
    shifted = p.copy()
    shifted[1] *= 1.02
    outcomes = iter([solver_result(p, cost=1.0), solver_result(shifted, cost=1.005), solver_result(p, cost=1.5)])
    monkeypatch.setattr(fitting, "least_squares", lambda *args, **kwargs: next(outcomes))
    near = fit_model_eis(freq, z, FitConfig(n_starts=3, near_best_rtol=rtol)).diagnostics["near_best"]
    assert near["start_indices"] == expected and near["start_count"] == len(expected)
    assert near["relative_cost_tolerance"] == rtol
    low, high = near["parameter_ranges"]["R0_Ohm"]
    assert low == pytest.approx(p[1])
    assert high == pytest.approx(shifted[1] if 1 in expected else p[1])


def test_near_best_tolerance_must_be_finite_and_non_negative():
    freq, _, z = spectrum()
    with pytest.raises(ValueError, match="near_best_rtol"):
        fit_model_eis(freq, z, FitConfig(near_best_rtol=-0.1))


@pytest.mark.parametrize("tail", ["cpe", "warburg"])
def test_every_reported_parameter_has_a_unit(monkeypatch, tail):
    freq, p, z = spectrum(tail)
    monkeypatch.setattr(fitting, "least_squares", lambda *args, **kwargs: solver_result(p))
    result = fit(freq, z, tail=tail, n_starts=1)
    assert list(parameter_units(tail)) == parameter_names(tail)
    assert result.parameter_units == parameter_units(tail)
    assert result.diagnostics["parameter_units"] == parameter_units(tail)


@pytest.mark.parametrize("tail", ["cpe", "warburg"])
def test_model_impedance_evaluates_named_parameters(tail):
    freq, p, z = spectrum(tail)
    named = dict(zip(parameter_names(tail), p))
    np.testing.assert_allclose(model_impedance(named, freq, tail), z)
    with pytest.raises(ValueError, match="missing"):
        model_impedance({name: value for name, value in named.items() if name != "R0_Ohm"}, freq, tail)


def test_plotting_options_are_separate_from_the_fit_configuration(tmp_path, monkeypatch):
    assert not {"save_png_dpi", "show_plot", "close_plot"} & {f.name for f in dataclasses.fields(FitConfig)}
    freq, p, z = spectrum()
    monkeypatch.setattr(fitting, "least_squares", lambda *args, **kwargs: solver_result(p))
    source = tmp_path / "sample.csv"
    write_csv(source, freq, z)
    result = process_file(source, cfg=FitConfig(n_starts=1), out_dir=tmp_path / "out", plot=PlotConfig(dpi=50))
    assert Path(result["outputs"]["png"]).is_file()
    payload = json.loads(Path(result["outputs"]["diagnostics"]).read_text())
    assert "save_png_dpi" not in payload["config"]
    assert payload["parameter_units"]["R0_Ohm"] == "Ohm"
    sheet = pd.read_excel(result["outputs"]["xlsx"], sheet_name="attempt_parameters")
    assert list(sheet["values"]) == ["start", "final"]


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
