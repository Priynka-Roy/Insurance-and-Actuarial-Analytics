"""Exercise public app paths against the actual saved, aggregate-only artifact."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app.main import SECTIONS

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("section", SECTIONS)
def test_all_saved_artifact_sections_render(section):
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    assert not app.exception
    app.sidebar.radio[0].set_value(section).run()
    assert not app.exception
    assert app.title[0].value == section
    assert not app.error
    assert not any("keyword arguments" in warning.value for warning in app.warning)


def test_group_filters_allow_empty_selection():
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    app.sidebar.radio[0].set_value("Portfolio Explorer").run()
    app.multiselect[0].set_value([]).run()
    assert not app.exception
    assert any("Select at least one group" in message.value for message in app.info)


def test_illustrative_quote_rejects_invalid_final_premium_shares():
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    app.sidebar.radio[0].set_value("Pure Premium & Pricing").run()
    app.number_input[1].set_value(0.8)
    app.number_input[3].set_value(0.8)
    app.run()
    assert not app.exception
    assert any("Invalid loading" in error.value for error in app.error)


def test_simulation_runs_only_after_submission_and_caches_result():
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=45).run()
    app.sidebar.radio[0].set_value("Portfolio Risk Simulator").run()
    assert "simulation_result" not in app.session_state
    app.number_input[0].set_value(50)
    next(widget for widget in app.selectbox if widget.label == "Simulated portfolios").set_value(1000)
    app.button[0].click().run()
    assert not app.exception
    assert not app.error
    result = app.session_state["simulation_result"]
    assert result["replicates"] == 1000
    assert len(result["losses"]) == 1000
    assert result["expected_loss"] >= 0
    assert result["es95"] >= result["var95"]


def test_missing_saved_artifact_has_actionable_message(monkeypatch, tmp_path):
    monkeypatch.setattr("app.main.ARTIFACT", tmp_path / "missing.json")
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    assert not app.exception
    assert any("offline pipeline" in error.value for error in app.error)


def test_corrupt_saved_artifact_reports_read_error(monkeypatch, tmp_path):
    artifact = tmp_path / "corrupt.json"
    artifact.write_text("{not JSON", encoding="utf-8")
    monkeypatch.setattr("app.main.ARTIFACT", artifact)
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    assert not app.exception
    assert any("could not be read" in error.value for error in app.error)


def test_saved_risk_summary_uses_full_sample_not_display_subset():
    import json
    from app.main import number
    data = json.loads((ROOT / "artifacts/dashboard.json").read_text())
    baseline = data["simulation"]["scenarios"][0]
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    app.sidebar.radio[0].set_value("Portfolio Risk Simulator").run()
    assert not app.exception
    assert any(baseline["plot_sample_note"] in item.value for item in app.caption)
    var_metric = next(metric for metric in app.metric if metric.label == "95% VaR")
    assert var_metric.value == number(baseline["var95"], 0)
    assert len(baseline["losses"]) < baseline["replicates"]


def test_profile_mix_preserves_exact_weighted_exposure_and_expected_loss():
    import json
    import numpy as np
    from app.main import synthetic_portfolio_inputs
    data = json.loads((ROOT / "artifacts/dashboard.json").read_text())
    cells = data["simulation_inputs"]["cells"]
    frequency, severity, exposure = synthetic_portfolio_inputs(cells, 1000)
    assert sum(exposure) == pytest.approx(1000)
    expected_loss = np.dot(np.asarray(frequency) * exposure, severity)
    assert expected_loss == pytest.approx(data["simulation"]["scenarios"][0]["expected_loss"])
    shifted = [{"frequency": 0.1, "severity": 100, "exposure": 0.5, "weight": 2},
               {"frequency": 0.2, "severity": 200, "exposure": 2.0, "weight": 1}]
    assert synthetic_portfolio_inputs(shifted, 100)[2] == pytest.approx((100 / 3, 400 / 6))


def test_missing_simulation_shape_does_not_supply_invented_default(monkeypatch, tmp_path):
    import json
    data = json.loads((ROOT / "artifacts/dashboard.json").read_text())
    data["simulation_inputs"].pop("gamma_shape")
    artifact = tmp_path / "incomplete.json"
    artifact.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr("app.main.ARTIFACT", artifact)
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    app.sidebar.radio[0].set_value("Portfolio Risk Simulator").run()
    assert not app.exception
    assert any("no replacement assumptions" in error.value for error in app.error)


def test_severity_deciles_display_claim_denominators_not_policy_exposure():
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    app.sidebar.radio[0].set_value("Claim Severity").run()
    assert not app.exception
    assert any("Grouped individual positive-payment claims" in item.value for item in app.caption)
    deciles = next(frame.value for frame in app.dataframe if "decile" in frame.value.columns)
    assert "claims" in deciles
    assert "claim_weight" in deciles
    assert "policies" not in deciles
    assert "exposure" not in deciles
    assert "observed_mean_payment" in deciles
    assert "predicted_mean_payment" in deciles
