"""Unit tests for the statistical inference and p-hacking module."""

import numpy as np
import pandas as pd
import pytest

from src.ephemeris import generate_ephemeris_df
from src.incidents import build_operational_panel
from src.stats import (
    analyze_real_statuspage_sample,
    build_client_explorer_payload,
    compare_binary_hypothesis,
    compute_naive_comparisons,
    fit_controlled_glm,
    permutation_test_diff_means,
    run_phacking_scan,
)


@pytest.fixture(scope="module")
def sample_merged_df() -> pd.DataFrame:
    panel = build_operational_panel("2024-01-01", "2024-12-31", seed=42)
    eph = generate_ephemeris_df("2024-01-01", "2024-12-31")
    return panel.merge(eph, on="date", how="inner")


def test_permutation_test_detects_strong_signal_and_null_noise() -> None:
    rng = np.random.default_rng(7)
    null_a = rng.poisson(3.0, size=100).astype(float)
    null_b = rng.poisson(3.0, size=100).astype(float)
    p_null = permutation_test_diff_means(null_a, null_b, n_perm=400, seed=1)
    assert 0.0 < p_null <= 1.0

    signal_a = rng.poisson(8.0, size=80).astype(float)
    signal_b = rng.poisson(2.0, size=80).astype(float)
    p_sig = permutation_test_diff_means(signal_a, signal_b, n_perm=400, seed=1)
    assert p_sig < 0.01


def test_compare_binary_hypothesis_metrics_are_consistent(sample_merged_df: pd.DataFrame) -> None:
    mask = sample_merged_df["is_weekend"].astype(bool)
    res = compare_binary_hypothesis(sample_merged_df, mask, n_perm=200, seed=5)
    assert res["n_exposed"] + res["n_baseline"] == len(sample_merged_df)
    assert res["rate_ratio"] < 0.5
    assert res["p_raw"] < 0.001
    assert res["p_perm"] < 0.01


def test_controlled_glm_identifies_weekend_confounder(sample_merged_df: pd.DataFrame) -> None:
    glm = fit_controlled_glm(sample_merged_df)
    terms = {t["term"]: t for t in glm["terms"]}
    assert glm["n_obs"] == len(sample_merged_df)
    assert terms["is_weekend_int"]["irr"] < 0.5
    assert terms["is_weekend_int"]["significant_at_05"] is True
    assert 0.5 < terms["is_mercury_retrograde"]["irr"] < 1.5


def test_phacking_scan_applies_multiple_testing_correction(sample_merged_df: pd.DataFrame) -> None:
    scan = run_phacking_scan(sample_merged_df, n_perm=200, seed=99)
    assert scan["total_hypotheses"] == 57
    for row in scan["hypotheses"]:
        assert row["q_fdr"] >= row["p_raw"] - 1e-6
        assert row["p_bonferroni"] >= row["p_raw"] - 1e-6
        assert 0.0 <= row["q_fdr"] <= 1.0
        assert 0.0 <= row["p_bonferroni"] <= 1.0


def test_compute_naive_comparisons_returns_expected_hypotheses(sample_merged_df: pd.DataFrame) -> None:
    results = compute_naive_comparisons(sample_merged_df, n_perm=100)
    assert len(results) == 5
    ids = {r["id"] for r in results}
    assert ids == {
        "mercury_retrograde",
        "mercury_pre_shadow",
        "mercury_post_shadow",
        "any_personal_retrograde",
        "full_moon",
    }
    for row in results:
        assert row["n_exposed"] + row["n_baseline"] == len(sample_merged_df)
        assert 0.0 <= row["p_raw"] <= 1.0


def test_analyze_real_statuspage_sample_empty_and_populated() -> None:
    empty_audit = analyze_real_statuspage_sample(pd.DataFrame())
    assert empty_audit == {"total_incidents": 0, "sources": 0, "tests": []}

    raw_df = pd.DataFrame(
        [
            {"incident_id": "1", "source": "github", "date": "2024-04-08"},
            {"incident_id": "2", "source": "github", "date": "2024-04-12"},
            {"incident_id": "3", "source": "vercel", "date": "2024-06-15"},
            {"incident_id": "4", "source": "vercel", "date": "2024-06-20"},
        ]
    )
    audit = analyze_real_statuspage_sample(raw_df)
    assert audit["total_incidents"] == 4
    assert audit["sources"] == 2
    assert len(audit["tests"]) == 3
    for test_entry in audit["tests"]:
        assert 0.0 <= test_entry["p_value"] <= 1.0


def test_build_client_explorer_payload_populates_all_slice_corrections(sample_merged_df: pd.DataFrame) -> None:
    scan = run_phacking_scan(sample_merged_df, n_perm=100, seed=42)
    payload = build_client_explorer_payload(sample_merged_df, scan)

    assert "any_personal_retrograde" in payload["options"]
    for opt in payload["options"].values():
        all_slice = opt["slices"]["all"]
        assert all_slice["q_fdr"] is not None
        assert all_slice["p_bonferroni"] is not None
        assert 0.0 <= all_slice["q_fdr"] <= 1.0
        assert 0.0 <= all_slice["p_bonferroni"] <= 1.0
        assert opt["slices"]["weekdays"]["q_fdr"] is None
        assert opt["slices"]["weekends"]["p_bonferroni"] is None
