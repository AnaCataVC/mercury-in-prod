"""Interactive Streamlit exploratory lab for mercury-in-prod."""

from __future__ import annotations

import json
from datetime import UTC, datetime, time
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.ephemeris import AstrologyEngine, ZodiacSign, generate_ephemeris_df
from src.incidents import build_and_save_dataset
from src.stats import (
    LUNAR_PHASES_EN_ES,
    PLANET_LABELS,
    STATE_LABELS,
    compare_binary_hypothesis,
    run_full_study,
)

DATA_DIR = Path("data")

THEME_COLORS: dict[str, str] = {
    "accent": "#38bdf8",
    "accent_2": "#f97316",
    "ok": "#10b981",
    "danger": "#ef4444",
    "muted": "#94a3b8",
    "null": "#64748b",
}


TEXT: dict[str, dict[str, str]] = {
    "en": {
        "title": "Mercury in Prod — Exploratory Ephemeris & Incidents Lab",
        "subtitle": (
            "Interactive statistical laboratory pairing an exact Python port of "
            "One UI Extra Widgets' AstrologyEngine with multi-year software incident dynamics."
        ),
        "lang_label": "Language",
        "dataset_header": "Dataset Overview",
        "tab_inspector": "Live Ephemeris Inspector",
        "tab_lab": "Hypothesis & Permutation Lab",
        "tab_phack": "P-Hacking & Multiple Testing",
        "date_pick": "Select UTC Date",
        "hour_pick": "UTC Hour",
        "sun_metric": "Sun Position",
        "moon_metric": "Lunar Phase & Illumination",
        "mercury_metric": "Mercury Status",
        "planets_heading": "Tracked Planetary Transits (Mercury – Saturn)",
        "speed_chart_title": "Mercury Apparent Daily Speed (+/- 90 Days Around Selected Date)",
        "lab_intro": (
            "Test any planetary or lunar hypothesis against production incident counts, "
            "apply calendar confounder filters, and run live Monte Carlo permutations."
        ),
        "filter_type": "Astronomical Dimension",
        "planet_select": "Planet",
        "state_select": "Motion State",
        "moon_select": "Lunar Phase",
        "sign_select": "Sun Sign",
        "outcome_select": "Incident Metric",
        "calendar_filter": "Calendar Confounder Slice",
        "perm_slider": "Monte Carlo Permutations",
        "exposed_days": "Exposed Days",
        "rate_ratio": "Incident Rate Ratio",
        "welch_p": "Welch t-test p",
        "mw_p": "Mann-Whitney p",
        "perm_p": "Permutation p",
        "dist_title": "Daily Metric Distribution: Exposed vs. Baseline",
        "phack_intro": (
            "When 57 astrological hypotheses are tested simultaneously, pure noise produces "
            "naive hits below p = 0.05. Applying Benjamini-Hochberg FDR and Bonferroni "
            "corrections filters out false discoveries."
        ),
        "volcano_title": "Multiple-Hypothesis Volcano Plot (57 Astrological Tests)",
        "real_audit_title": "Real Public Statuspage Incidents Audit (8 Engineering Platforms)",
    },
    "es": {
        "title": "Mercury in Prod — Laboratorio Exploratorio de Efemérides e Incidentes",
        "subtitle": (
            "Laboratorio estadístico interactivo que cruza una réplica exacta en Python de "
            "AstrologyEngine (One UI Extra Widgets) con series diarias de incidentes de software."
        ),
        "lang_label": "Idioma",
        "dataset_header": "Resumen del Dataset",
        "tab_inspector": "Inspector de Efemérides en Vivo",
        "tab_lab": "Laboratorio de Hipótesis y Permutaciones",
        "tab_phack": "Simulador de P-Hacking y Corrección FDR",
        "date_pick": "Fecha UTC",
        "hour_pick": "Hora UTC",
        "sun_metric": "Posición Solar",
        "moon_metric": "Fase e Iluminación Lunar",
        "mercury_metric": "Estado de Mercurio",
        "planets_heading": "Tránsitos Planetarios Rastreados (Mercurio – Saturno)",
        "speed_chart_title": "Velocidad Angular Diaria de Mercurio (+/- 90 Días)",
        "lab_intro": (
            "Pon a prueba cualquier hipótesis planetaria o lunar frente a los incidentes diarios, "
            "filtra por variables de calendario y ejecuta permutaciones de Monte Carlo en vivo."
        ),
        "filter_type": "Dimensión Astronómica",
        "planet_select": "Planeta",
        "state_select": "Estado Orbital",
        "moon_select": "Fase Lunar",
        "sign_select": "Signo Solar",
        "outcome_select": "Métrica de Incidentes",
        "calendar_filter": "Control de Calendario",
        "perm_slider": "Permutaciones de Monte Carlo",
        "exposed_days": "Días Expuestos",
        "rate_ratio": "Razón de Tasas (RR)",
        "welch_p": "p-value (Welch t)",
        "mw_p": "p-value (Mann-Whitney)",
        "perm_p": "p-value (Permutación)",
        "dist_title": "Distribución Diaria: Grupo Expuesto vs. Base",
        "phack_intro": (
            "Al evaluar 57 hipótesis astrológicas simultáneamente, el azar puro genera "
            "falsos hallazgos con p < 0.05. La corrección FDR de Benjamini-Hochberg y "
            "Bonferroni muestran qué sobrevive realmente."
        ),
        "volcano_title": "Gráfico Volcán de Múltiples Hipótesis (57 Pruebas)",
        "real_audit_title": "Auditoría de Incidentes Públicos Reales en Statuspage (8 Plataformas)",
    },
}


@st.cache_data(show_spinner="Loading ephemeris & incidents data...")
def load_project_data() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Load precomputed CSV/JSON datasets, building them if absent."""
    merged_path = DATA_DIR / "daily_incidents_ephemeris.csv"
    raw_path = DATA_DIR / "raw_public_incidents.csv"
    results_path = DATA_DIR / "study_results.json"

    if not merged_path.exists():
        build_and_save_dataset(data_dir=DATA_DIR)
    if not results_path.exists():
        run_full_study(data_dir=DATA_DIR)

    df = pd.read_csv(merged_path)
    raw_df = pd.read_csv(raw_path) if raw_path.exists() else pd.DataFrame()
    results = json.loads(results_path.read_text(encoding="utf-8"))
    return df, raw_df, results


def main() -> None:
    st.set_page_config(
        page_title="Mercury in Prod — Exploratory Lab",
        layout="wide",
    )

    df, raw_df, results = load_project_data()

    with st.sidebar:
        lang_choice = st.radio("Language / Idioma", options=["EN", "ES"], horizontal=True)
        lang = lang_choice.lower()
        t = TEXT[lang]
        is_es = lang == "es"

        st.divider()
        st.subheader(t["dataset_header"])
        summary = results["summary"]
        st.metric("Panel Days" if not is_es else "Días del Panel", f"{summary['panel_days']:,}")
        st.metric(
            "Real Statuspage Incidents" if not is_es else "Incidentes Reales Statuspage",
            f"{summary['real_public_incidents_count']:,} ({summary['real_public_sources_count']} APIs)",
        )
        st.metric(
            "Weekday vs Weekend Mean" if not is_es else "Media Laboral vs Fin de Semana",
            f"{summary['weekday_mean_incidents']:.2f} vs {summary['weekend_mean_incidents']:.2f}",
        )
        st.caption(f"{summary['start_date']} -> {summary['end_date']}")

    st.title(t["title"])
    st.markdown(t["subtitle"])

    tab1, tab2, tab3 = st.tabs([t["tab_inspector"], t["tab_lab"], t["tab_phack"]])

    # ------------------------------------------------------------------
    # Tab 1: Live Ephemeris Inspector
    # ------------------------------------------------------------------
    with tab1:
        col_d, col_h = st.columns([2, 1])
        with col_d:
            selected_date = st.date_input(
                t["date_pick"],
                value=datetime(2024, 4, 10, tzinfo=UTC).date(),
            )
        with col_h:
            selected_hour = st.slider(t["hour_pick"], min_value=0, max_value=23, value=12)

        target_dt = datetime.combine(selected_date, time(selected_hour, 0), tzinfo=UTC)
        snap = AstrologyEngine.compute_snapshot(target_dt)
        lunar = snap.lunar_status
        mercury = snap.mercury_status

        m1, m2, m3 = st.columns(3)
        m1.metric(
            t["sun_metric"],
            f"{snap.sun_sign.symbol} {snap.sun_sign.localized_name(is_es)}",
            f"{snap.sun_degree_in_sign:.2f}°",
        )
        m2.metric(
            t["moon_metric"],
            f"{lunar.localized_phase_name(is_es)} ({lunar.illumination_percent}%)",
            f"{lunar.moon_sign.symbol} {lunar.moon_sign.localized_name(is_es)} · {lunar.synodic_age_days:.1f}d",
        )
        m3.metric(
            t["mercury_metric"],
            mercury.motion_state.localized_badge(is_es),
            f"{mercury.daily_speed_deg:+.3f}°/d · {mercury.zodiac_sign.localized_name(is_es)}",
        )

        st.subheader(t["planets_heading"])
        planet_rows = [
            {
                "Planet": f"{p.symbol} {p.localized_name(is_es)}",
                "Sign": f"{p.zodiac_sign.symbol} {p.zodiac_sign.localized_name(is_es)}",
                "Degree": round(p.degree_in_sign, 2),
                "Daily Speed (°/d)": round(p.daily_speed_deg, 4),
                "Motion State": p.motion_state.localized_badge(is_es),
            }
            for p in snap.planets
        ]
        st.dataframe(pd.DataFrame(planet_rows), width="stretch", hide_index=True)

        # +/- 90 days Mercury speed window
        win_start = (pd.Timestamp(selected_date) - pd.Timedelta(days=90)).strftime("%Y-%m-%d")
        win_end = (pd.Timestamp(selected_date) + pd.Timedelta(days=90)).strftime("%Y-%m-%d")
        win_df = generate_ephemeris_df(win_start, win_end)
        fig_speed = px.line(
            win_df,
            x="date",
            y="mercury_daily_speed_deg",
            color="mercury_motion_state",
            title=t["speed_chart_title"],
            labels={"date": "UTC Date", "mercury_daily_speed_deg": "Speed (°/day)"},
        )
        fig_speed.add_hline(y=0.0, line_dash="dash", line_color=THEME_COLORS["danger"])
        fig_speed.add_vline(x=selected_date.strftime("%Y-%m-%d"), line_dash="dot", line_color=THEME_COLORS["muted"])
        st.plotly_chart(fig_speed, width="stretch")

    # ------------------------------------------------------------------
    # Tab 2: Interactive Hypothesis & Permutation Lab
    # ------------------------------------------------------------------
    with tab2:
        st.markdown(t["lab_intro"])
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            dim_options = {
                "planet": "Planetary Motion" if not is_es else "Movimiento Planetario",
                "moon": "Lunar Phase" if not is_es else "Fase Lunar",
                "sun_sign": "Sun Sign" if not is_es else "Signo Solar",
            }
            dim_key = st.selectbox(t["filter_type"], options=list(dim_options.keys()), format_func=lambda k: dim_options[k])

        with c2:
            if dim_key == "planet":
                planet_key = st.selectbox(
                    t["planet_select"],
                    options=list(PLANET_LABELS.keys()),
                    format_func=lambda k: PLANET_LABELS[k][1 if is_es else 0],
                )
            elif dim_key == "moon":
                moon_choice = st.selectbox(
                    t["moon_select"],
                    options=[p[0] for p in LUNAR_PHASES_EN_ES],
                    format_func=lambda en: next(p[1] if is_es else p[0] for p in LUNAR_PHASES_EN_ES if p[0] == en),
                )
            else:
                sun_choice = st.selectbox(
                    t["sign_select"],
                    options=[s.name_en for s in ZodiacSign],
                    format_func=lambda en: next(s.localized_name(is_es) for s in ZodiacSign if s.name_en == en),
                )

        outcome_map = {
            "incident_count": "Total Incidents / Day" if not is_es else "Incidentes Totales / Día",
            "critical_major_count": "Critical & Major / Day" if not is_es else "Críticos y Mayores / Día",
            "mean_duration_min": "Mean Duration (min)" if not is_es else "Duración Media (min)",
        }

        with c3:
            if dim_key == "planet":
                state_key = st.selectbox(
                    t["state_select"],
                    options=["RETROGRADE", "PRE_SHADOW", "POST_SHADOW", "DIRECT"],
                    format_func=lambda k: STATE_LABELS[k][1 if is_es else 0],
                )
            else:
                outcome_col = st.selectbox(
                    t["outcome_select"],
                    options=list(outcome_map.keys()),
                    format_func=lambda k: outcome_map[k],
                )

        with c4:
            cal_options = {
                "all": "All Days (Uncontrolled)" if not is_es else "Todos los días (Sin control)",
                "weekdays": "Weekdays Only (Mon–Fri)" if not is_es else "Solo laborales (Lun–Vie)",
                "midweek": "Midweek Deploy Window (Tue–Thu)" if not is_es else "Ventana Despliegues (Mar–Jue)",
                "weekends": "Weekends Only (Sat–Sun)" if not is_es else "Solo Fines de Semana",
            }
            cal_key = st.selectbox(t["calendar_filter"], options=list(cal_options.keys()), format_func=lambda k: cal_options[k])

        if dim_key == "planet":
            outcome_col = st.selectbox(
                t["outcome_select"],
                options=list(outcome_map.keys()),
                format_func=lambda k: outcome_map[k],
                key="planet_outcome",
            )

        n_perm = st.slider(t["perm_slider"], min_value=250, max_value=5000, value=1000, step=250)

        if cal_key == "weekdays":
            sub_df = df[~df["is_weekend"]].copy()
        elif cal_key == "midweek":
            sub_df = df[df["is_midweek_deploy_window"]].copy()
        elif cal_key == "weekends":
            sub_df = df[df["is_weekend"]].copy()
        else:
            sub_df = df.copy()

        if dim_key == "planet":
            mask = sub_df[f"{planet_key}_motion_state"] == state_key
        elif dim_key == "moon":
            mask = sub_df["moon_phase_name_en"] == moon_choice
        else:
            mask = sub_df["sun_sign"] == sun_choice

        stats_res = compare_binary_hypothesis(sub_df, mask, outcome_col=outcome_col, n_perm=n_perm, seed=42)

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric(t["exposed_days"], f"{stats_res['n_exposed']} / {len(sub_df)}")
        k2.metric(t["rate_ratio"], f"{stats_res['rate_ratio']:.3f}x", f"{stats_res['pct_diff']:+.1f}%")
        k3.metric(t["welch_p"], f"{stats_res['p_raw']:.4f}")
        k4.metric(t["mw_p"], f"{stats_res['mann_whitney_p']:.4f}")
        k5.metric(t["perm_p"], f"{stats_res['p_perm']:.4f}")

        plot_df = pd.DataFrame(
            {
                "value": sub_df[outcome_col],
                "Group": np.where(mask, "Exposed" if not is_es else "Expuesto", "Baseline" if not is_es else "Línea Base"),
            }
        )
        fig_dist = px.histogram(
            plot_df,
            x="value",
            color="Group",
            barmode="overlay",
            histnorm="percent",
            nbins=20,
            title=t["dist_title"],
            color_discrete_map={
                "Exposed": THEME_COLORS["accent_2"],
                "Expuesto": THEME_COLORS["accent_2"],
                "Baseline": THEME_COLORS["accent"],
                "Línea Base": THEME_COLORS["accent"],
            },
        )
        st.plotly_chart(fig_dist, width="stretch")

    # ------------------------------------------------------------------
    # Tab 3: Multiple Hypothesis Testing & Real Statuspage Audit
    # ------------------------------------------------------------------
    with tab3:
        st.markdown(t["phack_intro"])
        scan = results["phacking_scan"]
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Hypotheses Tested" if not is_es else "Hipótesis Evaluadas", scan["total_hypotheses"])
        s2.metric(
            "Expected Noise Hits (5%)" if not is_es else "Falsos Positivos Esperados (5%)",
            scan["expected_false_positives_at_05"],
        )
        s3.metric("Naive Hits (p < 0.05)" if not is_es else "Hits Ingenuos (p < 0.05)", scan["naive_hits_count"])
        s4.metric("FDR Survivors (q < 0.05)" if not is_es else "Sobrevivientes FDR (q < 0.05)", scan["fdr_survivors_count"])

        scan_df = pd.DataFrame(scan["hypotheses"])
        scan_df["Status"] = np.where(
            scan_df["survives_fdr"],
            "Survives FDR",
            np.where(scan_df["naive_hit"], "Naive Hit Only (False Positive)", "Null"),
        )
        fig_volcano = px.scatter(
            scan_df,
            x="log2_fold_change",
            y="neg_log10_p",
            color="Status",
            hover_data=["label_en", "rate_ratio", "p_raw", "q_fdr", "p_bonferroni", "n_exposed"],
            title=t["volcano_title"],
            color_discrete_map={
                "Survives FDR": THEME_COLORS["ok"],
                "Naive Hit Only (False Positive)": THEME_COLORS["accent_2"],
                "Null": THEME_COLORS["null"],
            },
        )
        fig_volcano.add_hline(
            y=-np.log10(0.05),
            line_dash="dash",
            line_color=THEME_COLORS["accent_2"],
            annotation_text="p = 0.05",
        )
        fig_volcano.add_hline(
            y=-np.log10(0.05 / scan["total_hypotheses"]),
            line_dash="dot",
            line_color=THEME_COLORS["danger"],
            annotation_text="Bonferroni",
        )
        st.plotly_chart(fig_volcano, width="stretch")

        display_cols = ["label_es" if is_es else "label_en", "family", "n_exposed", "rate_ratio", "p_raw", "q_fdr", "p_bonferroni", "p_perm", "naive_hit", "survives_fdr"]
        st.dataframe(scan_df[display_cols], width="stretch", hide_index=True)

        st.subheader(t["real_audit_title"])
        audit = results["real_statuspage_audit"]
        if audit.get("tests"):
            audit_df = pd.DataFrame(audit["tests"])
            st.dataframe(
                audit_df[["label_es" if is_es else "label_en", "observed_count", "expected_count", "observed_pct", "expected_pct", "p_value"]],
                width="stretch",
                hide_index=True,
            )
            if not raw_df.empty:
                with st.expander("Inspect Raw Statuspage Sources" if not is_es else "Ver Fuentes Statuspage"):
                    st.dataframe(raw_df.head(100), width="stretch", hide_index=True)


if __name__ == "__main__":
    main()
