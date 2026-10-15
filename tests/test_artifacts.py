"""Offline public-bundle consistency, preservation and tamper detection."""

from pathlib import Path
import hashlib
import json
import shutil
import pytest
from scripts.verify_artifacts import verify, REQUIRED

ROOT = Path(__file__).resolve().parents[1]


def fixture_bundle(tmp_path):
    for name in [*REQUIRED, "artifacts/manifest.json"]:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    return tmp_path


def reseal(root):
    manifest = root / "artifacts/manifest.json"
    bundle = json.loads(manifest.read_text())
    bundle["files"] = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in bundle["files"]
    }
    manifest.write_text(json.dumps(bundle))


def test_verified_public_bundle_has_consistent_actuarial_denominators():
    assert verify() == 6
    r = json.loads((ROOT / "artifacts/dashboard.json").read_text())
    s = r["summary"]
    assert s["frequency"] * s["severity"] == pytest.approx(s["pure_premium"])
    assert s["claims"] / s["exposure_years"] == pytest.approx(s["frequency"])
    assert s["claim_amount"] == r["audit"]["primary_claim_amount"]
    assert s["policies"] == sum(v["policies"] for v in r["validation"]["split_summary"].values())
    assert {c["id"] for c in r["case_studies"]} == set("ABCDEFGH")
    assert r["selection"]["test_used_for_selection"] is False
    for task, key in [
        ("frequency", "poisson_deviance_per_exposure"),
        ("severity", "gamma_deviance"),
        ("pure_premium", "tweedie_deviance_p1_5"),
    ]:
        rows = r["models"][task]
        selected = [row for row in rows if row["selected"]]
        assert len(selected) == 1
        assert selected[0]["validation"][key] == min(row["validation"][key] for row in rows)
    for rows in r["segments"].values():
        assert sum(row["policies"] for row in rows) == r["validation"]["split_summary"]["test"]["policies"]
    assert all("IDpol" not in p for p in r["profiles"])
    assert all("claims" in row and "policies" not in row and "exposure" not in row for row in r["validation"]["severity_deciles"])


def test_saved_scenarios_respect_marginal_and_pricing_arithmetic():
    r = json.loads((ROOT / "artifacts/dashboard.json").read_text())
    rows = r["simulation"]["scenarios"]
    base, frequency, severity, combined, alternate, shock, mix = rows
    for row in rows:
        assert abs(row["mean"] - row["expected_loss"]) < 4 * row["mean_se"]
        assert row["var95"] <= row["es95"]
        assert row["var99"] <= row["es99"]
        assert row["expected_loss_ratio"] == pytest.approx(row["expected_loss"] / row["assumed_premium"])
        assert len(row["losses"]) == row["plot_sample_size"] < row["replicates"]
    assert alternate["expected_loss"] == shock["expected_loss"] == base["expected_loss"]
    assert frequency["expected_loss"] == pytest.approx(1.2 * base["expected_loss"])
    assert severity["expected_loss"] == pytest.approx(1.2 * base["expected_loss"])
    assert combined["expected_loss"] == pytest.approx(1.44 * base["expected_loss"])
    assert mix["expected_loss"] != base["expected_loss"]


def test_changed_bytes_rejected(tmp_path):
    root = fixture_bundle(tmp_path)
    with (root / "artifacts/dashboard.json").open("a") as handle:
        handle.write(" ")
    with pytest.raises(ValueError, match="Integrity failure"):
        verify(root)


def test_resealed_inconsistent_selection_rejected(tmp_path):
    root = fixture_bundle(tmp_path)
    p = root / "reports/selection_frozen.json"
    data = json.loads(p.read_text())
    data["frequency"] = "invented"
    p.write_text(json.dumps(data))
    reseal(root)
    with pytest.raises(ValueError, match="Frozen selection"):
        verify(root)


def test_protocol_change_even_resealed_is_rejected(tmp_path):
    root = fixture_bundle(tmp_path)
    p = root / "configs/protocol.json"
    p.write_text(p.read_text() + " ")
    reseal(root)
    with pytest.raises(ValueError, match="protocol fingerprint"):
        verify(root)


@pytest.mark.parametrize(
    "path", ["../escape.json", "/tmp/escape.json", "artifacts/../escape.json", "artifacts/model.pkl"]
)
def test_unsafe_manifest_paths_rejected(tmp_path, path):
    root = fixture_bundle(tmp_path)
    p = root / "artifacts/manifest.json"
    d = json.loads(p.read_text())
    d["files"][path] = "a" * 64
    p.write_text(json.dumps(d))
    with pytest.raises(ValueError, match="Unsafe or unsupported"):
        verify(root)


def test_symlink_rejected(tmp_path):
    root = fixture_bundle(tmp_path)
    p = root / "artifacts/dashboard.json"
    p.unlink()
    p.symlink_to(ROOT / "artifacts/dashboard.json")
    with pytest.raises(ValueError, match="Symlink"):
        verify(root)
