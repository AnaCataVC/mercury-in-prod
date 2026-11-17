"""Statistical inference, confounder-controlled GLM, and p-hacking simulation."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats as sp_stats
from statsmodels.stats.multitest import multipletests

from src.ephemeris import (
    LUNAR_PHASES_EN_ES,
    PLANET_LABELS,
    STATE_LABELS,
    ZodiacSign,
    generate_ephemeris_df,
)


def permutation_test_diff_means(
    x_exposed: np.ndarray,
    x_baseline: np.ndarray,
    n_perm: int = 1000,
    seed: int = 42,
) -> float:
    """Compute a two-sided vectorized Monte Carlo permutation p-value for mean difference."""
    n_exp = len(x_exposed)
    n_base = len(x_baseline)
    if n_exp == 0 or n_base == 0:
        return 1.0

    observed_diff = abs(float(np.mean(x_exposed) - np.mean(x_baseline)))
    pooled = np.concatenate([x_exposed, x_baseline])
    total_sum = float(np.sum(pooled))
    n_total = len(pooled)

    rng = np.random.default_rng(seed)
    # Draw random permutations efficiently via argsort of uniform noise
    noise = rng.random((n_perm, n_total))
    idx = np.argpartition(noise, kth=n_exp - 1, axis=1)[:, :n_exp]
    perm_exp_means = np.mean(pooled[idx], axis=1)
    perm_base_means = (total_sum - np.sum(pooled[idx], axis=1)) / n_base
    perm_diffs = np.abs(perm_exp_means - perm_base_means)

    exceedances = int(np.sum(perm_diffs >= observed_diff - 1e-12))
    return float((exceedances + 1) / (n_perm + 1))


def compare_binary_hypothesis(
    df: pd.DataFrame,
    mask: pd.Series,
    outcome_col: str = "incident_count",
    n_perm: int = 1000,
    seed: int = 42,
) -> dict[str, Any]:
    """Evaluate an exposed vs baseline boolean mask with Welch, Mann-Whitney, and permutation tests."""
    exposed = df.loc[mask, outcome_col].to_numpy(dtype=float)
    baseline = df.loc[~mask, outcome_col].to_numpy(dtype=float)

    n_exp = len(exposed)
    n_base = len(baseline)
    if n_exp < 2 or n_base < 2:
        return {
            "n_exposed": n_exp,
            "n_baseline": n_base,
            "mean_exposed": float(np.mean(exposed)) if n_exp else 0.0,
            "mean_baseline": float(np.mean(baseline)) if n_base else 0.0,
            "std_exposed": 0.0,
            "std_baseline": 0.0,
            "rate_ratio": 1.0,
            "pct_diff": 0.0,
            "welch_t_stat": 0.0,
            "p_raw": 1.0,
            "mann_whitney_u": 0.0,
            "mann_whitney_p": 1.0,
            "p_perm": 1.0,
        }

    mean_exp = float(np.mean(exposed))
    mean_base = float(np.mean(baseline))
    rate_ratio = mean_exp / mean_base if mean_base > 0 else 1.0
    pct_diff = (rate_ratio - 1.0) * 100.0

    t_res = sp_stats.ttest_ind(exposed, baseline, equal_var=False)
    mw_res = sp_stats.mannwhitneyu(exposed, baseline, alternative="two-sided")
    p_raw = float(t_res.pvalue) if not math.isnan(float(t_res.pvalue)) else 1.0
    p_mw = float(mw_res.pvalue) if not math.isnan(float(mw_res.pvalue)) else 1.0
    p_perm = permutation_test_diff_means(exposed, baseline, n_perm=n_perm, seed=seed)

    return {
        "n_exposed": n_exp,
        "n_baseline": n_base,
        "mean_exposed": round(mean_exp, 4),
        "mean_baseline": round(mean_base, 4),
        "std_exposed": round(float(np.std(exposed, ddof=1)), 4),
        "std_baseline": round(float(np.std(baseline, ddof=1)), 4),
        "rate_ratio": round(rate_ratio, 4),
        "pct_diff": round(pct_diff, 2),
        "welch_t_stat": round(float(t_res.statistic), 4) if not math.isnan(float(t_res.statistic)) else 0.0,
        "p_raw": round(p_raw, 6),
        "mann_whitney_u": round(float(mw_res.statistic), 2),
        "mann_whitney_p": round(p_mw, 6),
        "p_perm": round(p_perm, 6),
    }


def compute_naive_comparisons(df: pd.DataFrame, n_perm: int = 1000) -> list[dict[str, Any]]:
    """Compute naive unadjusted comparisons for headline astrological hypotheses."""
    specs: list[tuple[str, str, str, pd.Series]] = [
        ("mercury_retrograde", "Mercury Retrograde", "Mercurio Retrógrado", df["mercury_is_retrograde"].astype(bool)),
        ("mercury_pre_shadow", "Mercury Pre-Shadow", "Pre-Sombra de Mercurio", df["mercury_is_pre_shadow"].astype(bool)),
        ("mercury_post_shadow", "Mercury Post-Shadow", "Post-Sombra de Mercurio", df["mercury_is_post_shadow"].astype(bool)),
        (
            "any_personal_retrograde",
            "Any Personal Planet Retrograde",
            "Cualquier Planeta Personal Retrógrado",
            df["any_personal_retrograde"].astype(bool),
        ),
        ("full_moon", "Full Moon", "Luna Llena", df["is_full_moon"].astype(bool)),
    ]

    results: list[dict[str, Any]] = []
    for idx, (hyp_id, label_en, label_es, mask) in enumerate(specs):
        metrics = compare_binary_hypothesis(df, mask, outcome_col="incident_count", n_perm=n_perm, seed=100 + idx)
        results.append({"id": hyp_id, "label_en": label_en, "label_es": label_es, **metrics})
    return results


def fit_controlled_glm(df: pd.DataFrame) -> dict[str, Any]:
    """Fit a confounder-controlled Poisson GLM with HC3 robust standard errors."""
    model_df = df.copy()
    model_df["is_mercury_retrograde"] = model_df["mercury_is_retrograde"].astype(int)
    model_df["is_mercury_shadow"] = (
        model_df["mercury_is_pre_shadow"].astype(bool) | model_df["mercury_is_post_shadow"].astype(bool)
    ).astype(int)
    model_df["is_full_moon_int"] = model_df["is_full_moon"].astype(int)
    model_df["moon_illumination"] = model_df["moon_illumination_fraction"].astype(float)
    model_df["is_weekend_int"] = model_df["is_weekend"].astype(int)
    model_df["is_midweek_deploy_int"] = model_df["is_midweek_deploy_window"].astype(int)
    model_df["is_code_freeze_int"] = model_df["is_code_freeze"].astype(int)
    model_df["is_patch_tuesday_int"] = model_df["is_patch_tuesday"].astype(int)

    rhs_terms = [
        "is_mercury_retrograde",
        "is_mercury_shadow",
        "is_full_moon_int",
        "moon_illumination",
        "is_weekend_int",
        "is_midweek_deploy_int",
        "is_code_freeze_int",
        "is_patch_tuesday_int",
    ]
    active_rhs = [col for col in rhs_terms if model_df[col].nunique() > 1]
    if model_df["month"].nunique() > 1:
        active_rhs.append("C(month)")
    if "year_z" in model_df.columns and float(model_df["year_z"].std()) > 1e-9:
        active_rhs.append("year_z")

    formula = "incident_count ~ " + " + ".join(active_rhs)
    glm_res = smf.glm(formula=formula, data=model_df, family=sm.families.Poisson()).fit(cov_type="HC3")

    conf_int = glm_res.conf_int()
    term_meta: list[tuple[str, str, str, str]] = [
        ("is_weekend_int", "Weekend (Sat–Sun)", "Fin de semana (Sáb–Dom)", "engineering"),
        ("is_midweek_deploy_int", "Midweek Deploy Window (Tue–Thu)", "Ventana de despliegues (Mar–Jue)", "engineering"),
        ("is_code_freeze_int", "Q4 Code Freeze (Dec 20–Jan 2)", "Code Freeze Q4 (20 Dic–2 Ene)", "engineering"),
        ("is_patch_tuesday_int", "Patch Tuesday (2nd Tue/mo)", "Patch Tuesday (2.º martes/mes)", "engineering"),
        ("is_mercury_retrograde", "Mercury Retrograde", "Mercurio Retrógrado", "astrology"),
        ("is_mercury_shadow", "Mercury Pre/Post Shadow", "Sombra Pre/Post de Mercurio", "astrology"),
        ("is_full_moon_int", "Full Moon", "Luna Llena", "astrology"),
        ("moon_illumination", "Lunar Illumination (0 -> 1)", "Iluminación Lunar (0 -> 1)", "astrology"),
    ]

    forest_rows: list[dict[str, Any]] = []
    for term, label_en, label_es, category in term_meta:
        if term not in glm_res.params:
            continue
        coef = float(glm_res.params[term])
        ci_low = float(conf_int.loc[term, 0])
        ci_high = float(conf_int.loc[term, 1])
        pval = float(glm_res.pvalues[term])
        forest_rows.append(
            {
                "term": term,
                "label_en": label_en,
                "label_es": label_es,
                "category": category,
                "beta": round(coef, 4),
                "irr": round(math.exp(coef), 4),
                "ci_low": round(math.exp(ci_low), 4),
                "ci_high": round(math.exp(ci_high), 4),
                "p_value": round(pval, 6),
                "significant_at_05": bool(pval < 0.05),
            }
        )

    pearson_dispersion = float(glm_res.pearson_chi2 / max(1, glm_res.df_resid))
    return {
        "model_type": "Poisson GLM with HC3 robust standard errors",
        "n_obs": int(glm_res.nobs),
        "aic": round(float(glm_res.aic), 2),
        "deviance": round(float(glm_res.deviance), 2),
        "pearson_dispersion": round(pearson_dispersion, 3),
        "terms": forest_rows,
    }


def analyze_real_statuspage_sample(
    raw_df: pd.DataFrame,
    ephemeris_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Audit real fetched Statuspage incidents against per-provider astronomical base rates."""
    if raw_df.empty:
        return {"total_incidents": 0, "sources": 0, "tests": []}

    min_d = str(raw_df["date"].min())
    max_d = str(raw_df["date"].max())
    eph = ephemeris_df if ephemeris_df is not None else generate_ephemeris_df(min_d, max_d)
    if eph["date"].min() > min_d or eph["date"].max() < max_d:
        eph = generate_ephemeris_df(min(min_d, str(eph["date"].min())), max(max_d, str(eph["date"].max())))

    joined = raw_df.merge(
        eph[["date", "mercury_is_retrograde", "mercury_motion_state", "is_full_moon"]],
        on="date",
        how="inner",
    )
    if joined.empty:
        return {"total_incidents": 0, "sources": 0, "tests": []}

    # Compute source-window-weighted expected astronomical base rates
    source_counts = joined["source"].value_counts()
    total_n = len(joined)
    exp_retro_num = 0.0
    exp_full_moon_num = 0.0
    exp_shadow_num = 0.0

    for src, cnt in source_counts.items():
        sub_dates = joined.loc[joined["source"] == src, "date"]
        s_min = str(sub_dates.min())
        s_max = str(sub_dates.max())
        window_eph = eph[(eph["date"] >= s_min) & (eph["date"] <= s_max)]
        if window_eph.empty:
            continue
        exp_retro_num += cnt * float(window_eph["mercury_is_retrograde"].mean())
        exp_full_moon_num += cnt * float(window_eph["is_full_moon"].mean())
        exp_shadow_num += cnt * float(window_eph["mercury_motion_state"].isin(["PRE_SHADOW", "POST_SHADOW"]).mean())

    def _binom_entry(test_id: str, label_en: str, label_es: str, observed: int, expected: float) -> dict[str, Any]:
        p_exp = max(1e-6, min(1.0 - 1e-6, expected / total_n))
        res = sp_stats.binomtest(observed, n=total_n, p=p_exp, alternative="two-sided")
        return {
            "id": test_id,
            "label_en": label_en,
            "label_es": label_es,
            "observed_count": int(observed),
            "expected_count": round(expected, 2),
            "observed_pct": round(100.0 * observed / total_n, 2),
            "expected_pct": round(100.0 * p_exp, 2),
            "p_value": round(float(res.pvalue), 6),
        }

    obs_retro = int(joined["mercury_is_retrograde"].sum())
    obs_shadow = int(joined["mercury_motion_state"].isin(["PRE_SHADOW", "POST_SHADOW"]).sum())
    obs_full = int(joined["is_full_moon"].sum())

    return {
        "total_incidents": total_n,
        "sources": int(joined["source"].nunique()),
        "date_range": [str(joined["date"].min()), str(joined["date"].max())],
        "tests": [
            _binom_entry("real_mercury_retrograde", "Mercury Retrograde", "Mercurio Retrógrado", obs_retro, exp_retro_num),
            _binom_entry("real_mercury_shadow", "Mercury Pre/Post Shadow", "Sombra de Mercurio", obs_shadow, exp_shadow_num),
            _binom_entry("real_full_moon", "Full Moon", "Luna Llena", obs_full, exp_full_moon_num),
        ],
    }


def _collect_phacking_hypotheses(df: pd.DataFrame) -> list[tuple[str, str, str, str, pd.Series, str]]:
    """Build 55+ astrological hypotheses across planets, lunar phases, zodiac signs, and slices."""
    specs: list[tuple[str, str, str, str, pd.Series, str]] = []

    # 1. 5 planets x 3 non-direct states (15 hypotheses)
    for planet_key, (p_en, p_es) in PLANET_LABELS.items():
        for state_key in ("RETROGRADE", "PRE_SHADOW", "POST_SHADOW"):
            s_en, s_es = STATE_LABELS[state_key]
            mask = df[f"{planet_key}_motion_state"] == state_key
            specs.append(
                (
                    f"{planet_key}_{state_key.lower()}",
                    f"{p_en}: {s_en}",
                    f"{p_es}: {s_es}",
                    "Planetary Motion",
                    mask,
                    "incident_count",
                )
            )

    # 2. 8 lunar phases (8 hypotheses)
    for phase_en, phase_es in LUNAR_PHASES_EN_ES:
        mask = df["moon_phase_name_en"] == phase_en
        specs.append(
            (
                f"moon_phase_{phase_en.lower().replace(' ', '_')}",
                f"Moon Phase: {phase_en}",
                f"Fase Lunar: {phase_es}",
                "Lunar Phase",
                mask,
                "incident_count",
            )
        )

    # 3. 12 Sun signs (12 hypotheses)
    for sign in ZodiacSign:
        mask = df["sun_sign"] == sign.name_en
        specs.append(
            (
                f"sun_in_{sign.name_en.lower()}",
                f"Sun in {sign.name_en}",
                f"Sol en {sign.name_es}",
                "Sun Sign",
                mask,
                "incident_count",
            )
        )

    # 4. 12 Moon signs (12 hypotheses)
    for sign in ZodiacSign:
        mask = df["moon_sign"] == sign.name_en
        specs.append(
            (
                f"moon_in_{sign.name_en.lower()}",
                f"Moon in {sign.name_en}",
                f"Luna en {sign.name_es}",
                "Moon Sign",
                mask,
                "incident_count",
            )
        )

    # 5. 10 targeted subgroup / severity / weekday slices (classic p-hacking moves)
    subgroup_defs: list[tuple[str, str, str, pd.Series, str]] = [
        (
            "mercury_retro_fridays",
            "Mercury Retrograde on Fridays",
            "Mercurio Retrógrado en Viernes",
            df["mercury_is_retrograde"].astype(bool) & df["is_friday"].astype(bool),
            "incident_count",
        ),
        (
            "mercury_retro_mondays",
            "Mercury Retrograde on Mondays",
            "Mercurio Retrógrado en Lunes",
            df["mercury_is_retrograde"].astype(bool) & (df["day_of_week"] == 0),
            "incident_count",
        ),
        (
            "mercury_retro_critical",
            "Mercury Retrograde (Critical/Major)",
            "Mercurio Retrógrado (Críticos/Mayores)",
            df["mercury_is_retrograde"].astype(bool),
            "critical_major_count",
        ),
        (
            "mars_retro_critical",
            "Mars Retrograde (Critical/Major)",
            "Marte Retrógrado (Críticos/Mayores)",
            df["mars_is_retrograde"].astype(bool),
            "critical_major_count",
        ),
        (
            "full_moon_weekdays",
            "Full Moon on Weekdays",
            "Luna Llena en Días Laborales",
            df["is_full_moon"].astype(bool) & (~df["is_weekend"].astype(bool)),
            "incident_count",
        ),
        (
            "new_moon_critical",
            "New Moon (Critical/Major)",
            "Luna Nueva (Críticos/Mayores)",
            df["is_new_moon"].astype(bool),
            "critical_major_count",
        ),
        (
            "venus_retro_critical",
            "Venus Retrograde (Critical/Major)",
            "Venus Retrógrado (Críticos/Mayores)",
            df["venus_is_retrograde"].astype(bool),
            "critical_major_count",
        ),
        (
            "saturn_retro_critical",
            "Saturn Retrograde (Critical/Major)",
            "Saturno Retrógrado (Críticos/Mayores)",
            df["saturn_is_retrograde"].astype(bool),
            "critical_major_count",
        ),
        (
            "three_plus_retrogrades",
            "3+ Planets Simultaneously Retrograde",
            "3+ Planetas Retrógrados Simultáneos",
            df["any_retrograde_count"] >= 3,
            "incident_count",
        ),
        (
            "mercury_in_fire_signs",
            "Mercury in Fire Signs",
            "Mercurio en Signos de Fuego",
            df["mercury_sign"].isin(["Aries", "Leo", "Sagittarius"]),
            "incident_count",
        ),
    ]
    for hyp_id, en, es, mask, outcome in subgroup_defs:
        specs.append((hyp_id, en, es, "Subgroup Slice", mask, outcome))

    return specs


def run_phacking_scan(df: pd.DataFrame, n_perm: int = 1000, seed: int = 42) -> dict[str, Any]:
    """Run 57 astrological hypotheses and apply BH-FDR and Bonferroni corrections."""
    specs = _collect_phacking_hypotheses(df)
    rows: list[dict[str, Any]] = []

    for idx, (hyp_id, label_en, label_es, family, mask, outcome_col) in enumerate(specs):
        metrics = compare_binary_hypothesis(df, mask, outcome_col=outcome_col, n_perm=n_perm, seed=seed + idx)
        rr = max(1e-6, metrics["rate_ratio"])
        log2_fc = math.log2(rr)
        p_raw = max(1e-12, metrics["p_raw"])
        rows.append(
            {
                "id": hyp_id,
                "label_en": label_en,
                "label_es": label_es,
                "family": family,
                "outcome_col": outcome_col,
                **metrics,
                "log2_fold_change": round(log2_fc, 4),
                "neg_log10_p": round(-math.log10(p_raw), 4),
            }
        )

    p_values = [r["p_raw"] for r in rows]
    reject_fdr, q_fdr, _, _ = multipletests(p_values, alpha=0.05, method="fdr_bh")
    reject_bonf, p_bonf, _, _ = multipletests(p_values, alpha=0.05, method="bonferroni")

    for row, q_val, r_fdr, b_val, r_bonf in zip(rows, q_fdr, reject_fdr, p_bonf, reject_bonf):
        row["q_fdr"] = round(float(q_val), 6)
        row["p_bonferroni"] = round(float(b_val), 6)
        row["naive_hit"] = bool(row["p_raw"] < 0.05)
        row["survives_fdr"] = bool(r_fdr)
        row["survives_bonferroni"] = bool(r_bonf)

    rows.sort(key=lambda r: r["p_raw"])
    naive_hits = sum(1 for r in rows if r["naive_hit"])
    fdr_hits = sum(1 for r in rows if r["survives_fdr"])
    bonf_hits = sum(1 for r in rows if r["survives_bonferroni"])

    return {
        "total_hypotheses": len(rows),
        "expected_false_positives_at_05": round(len(rows) * 0.05, 2),
        "naive_hits_count": naive_hits,
        "fdr_survivors_count": fdr_hits,
        "bonferroni_survivors_count": bonf_hits,
        "hypotheses": rows,
    }


def _histogram_distribution(values: np.ndarray, max_bin: int = 12) -> list[float]:
    """Return normalized percentage distribution across integer incident count bins 0..max_bin."""
    clipped = np.clip(values.astype(int), 0, max_bin)
    counts = np.bincount(clipped, minlength=max_bin + 1)
    total = float(np.sum(counts)) or 1.0
    return [round(float(c / total * 100.0), 2) for c in counts]


def build_client_explorer_payload(
    df: pd.DataFrame,
    scan_results: dict[str, Any],
) -> dict[str, Any]:
    """Precompute filterable hypothesis statistics for the client-side web explorer."""
    fdr_lookup = {h["id"]: h["q_fdr"] for h in scan_results["hypotheses"]}
    bonf_lookup = {h["id"]: h["p_bonferroni"] for h in scan_results["hypotheses"]}
    scan_p_values = [float(h["p_raw"]) for h in scan_results["hypotheses"]]
    n_scan = max(1, len(scan_p_values))

    options: list[tuple[str, str, str, pd.Series]] = []
    for planet_key, (p_en, p_es) in PLANET_LABELS.items():
        for state_key in ("RETROGRADE", "PRE_SHADOW", "POST_SHADOW"):
            s_en, s_es = STATE_LABELS[state_key]
            options.append(
                (
                    f"{planet_key}_{state_key.lower()}",
                    f"{p_en} — {s_en}",
                    f"{p_es} — {s_es}",
                    df[f"{planet_key}_motion_state"] == state_key,
                )
            )

    options.append(("moon_phase_full_moon", "Moon — Full Moon", "Luna — Luna Llena", df["is_full_moon"].astype(bool)))
    options.append(("moon_phase_new_moon", "Moon — New Moon", "Luna — Luna Nueva", df["is_new_moon"].astype(bool)))
    options.append(
        (
            "any_personal_retrograde",
            "Any Personal Planet Retrograde",
            "Cualquier Planeta Personal Retrógrado",
            df["any_personal_retrograde"].astype(bool),
        )
    )

    slices: dict[str, pd.Series] = {
        "all": pd.Series(True, index=df.index),
        "weekdays": ~df["is_weekend"].astype(bool),
        "weekends": df["is_weekend"].astype(bool),
    }

    records: dict[str, dict[str, Any]] = {}
    for opt_id, label_en, label_es, base_mask in options:
        slice_data: dict[str, Any] = {}
        for slice_name, slice_mask in slices.items():
            sub_df = df.loc[slice_mask]
            sub_mask = base_mask.loc[slice_mask]
            stats_dict = compare_binary_hypothesis(sub_df, sub_mask, outcome_col="incident_count", n_perm=500, seed=77)
            exp_vals = sub_df.loc[sub_mask, "incident_count"].to_numpy()
            base_vals = sub_df.loc[~sub_mask, "incident_count"].to_numpy()

            if slice_name == "all":
                q_val = fdr_lookup.get(opt_id)
                bonf_val = bonf_lookup.get(opt_id)
                if q_val is None and scan_p_values:
                    _, q_arr, _, _ = multipletests(
                        scan_p_values + [float(stats_dict["p_raw"])],
                        alpha=0.05,
                        method="fdr_bh",
                    )
                    q_val = round(float(q_arr[-1]), 6)
                if bonf_val is None:
                    bonf_val = round(min(1.0, float(stats_dict["p_raw"]) * n_scan), 6)
            else:
                q_val = None
                bonf_val = None

            slice_data[slice_name] = {
                **stats_dict,
                "q_fdr": q_val,
                "p_bonferroni": bonf_val,
                "exposed_hist_pct": _histogram_distribution(exp_vals),
                "baseline_hist_pct": _histogram_distribution(base_vals),
            }
        records[opt_id] = {
            "id": opt_id,
            "label_en": label_en,
            "label_es": label_es,
            "slices": slice_data,
        }

    return {"bins": [str(i) for i in range(12)] + ["12+"], "options": records}


def run_full_study(
    data_dir: Path | str = Path("data"),
    n_perm: int = 1000,
) -> dict[str, Any]:
    """Load merged dataset, execute all statistical modules, and save ``study_results.json``."""
    base_dir = Path(data_dir)
    merged_path = base_dir / "daily_incidents_ephemeris.csv"
    raw_path = base_dir / "raw_public_incidents.csv"

    df = pd.read_csv(merged_path)
    raw_df = pd.read_csv(raw_path) if raw_path.exists() else pd.DataFrame()
    eph_cols = [c for c in df.columns if c in {"date", "mercury_is_retrograde", "mercury_motion_state", "is_full_moon"}]
    eph_sub = df[eph_cols] if len(eph_cols) == 4 else None

    naive = compute_naive_comparisons(df, n_perm=n_perm)
    glm = fit_controlled_glm(df)
    scan = run_phacking_scan(df, n_perm=n_perm)
    real_audit = analyze_real_statuspage_sample(raw_df, ephemeris_df=eph_sub)
    explorer = build_client_explorer_payload(df, scan)

    timeline_cols = [
        "date",
        "incident_count",
        "critical_major_count",
        "is_weekend",
        "mercury_daily_speed_deg",
        "mercury_motion_state",
        "moon_illumination_percent",
        "moon_phase_name_en",
    ]
    timeline = df[timeline_cols].to_dict(orient="records")

    summary = {
        "panel_days": len(df),
        "start_date": str(df["date"].min()),
        "end_date": str(df["date"].max()),
        "total_panel_incidents": int(df["incident_count"].sum()),
        "mean_daily_incidents": round(float(df["incident_count"].mean()), 3),
        "weekday_mean_incidents": round(float(df.loc[~df["is_weekend"], "incident_count"].mean()), 3),
        "weekend_mean_incidents": round(float(df.loc[df["is_weekend"], "incident_count"].mean()), 3),
        "mercury_retrograde_days": int(df["mercury_is_retrograde"].sum()),
        "mercury_retrograde_pct": round(float(df["mercury_is_retrograde"].mean() * 100.0), 2),
        "real_public_incidents_count": len(raw_df),
        "real_public_sources_count": int(raw_df["source"].nunique()) if not raw_df.empty else 0,
    }

    payload: dict[str, Any] = {
        "summary": summary,
        "naive_comparisons": naive,
        "controlled_glm": glm,
        "real_statuspage_audit": real_audit,
        "phacking_scan": scan,
        "explorer": explorer,
        "timeline": timeline,
    }

    out_path = base_dir / "study_results.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
